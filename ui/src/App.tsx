import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Activity, PlayCircle, PauseCircle } from 'lucide-react';
import { Toaster, toast } from 'sonner';

import { ForexChart, type PriceTarget } from './components/ForexChart';
import { StrategySelector, type Strategy } from './components/StrategySelector';
import { SignalLogs, type SignalLog } from './components/SignalLogs';
import { InstrumentSelector } from './components/InstrumentSelector';
import { PredictionPanel, type PredictionData } from './components/PredictionPanel';
import { Button } from './components/ui/button';
import {
  fetchCandles,
  fetchPrediction,
  fetchSignals,
  fetchStrategies,
  enableStrategy,
  disableStrategy,
  type CandlePoint,
  type SignalResponse,
  type Strategy as ApiStrategy,
} from './lib/api';
import { connectMarketStream, type MarketMessage } from './lib/marketBus';

const TIMEFRAME = 60;
const CANDLE_LIMIT = 300;

const statusMap: Record<NonNullable<SignalResponse['result']>, SignalLog['status']> = {
  OPEN: 'ACTIVE',
  WIN: 'CLOSED',
  LOSS: 'STOPPED',
  BE: 'BE',
};

const resultMap: Partial<Record<NonNullable<SignalResponse['result']>, SignalLog['result']>> = {
  WIN: 'WIN',
  LOSS: 'LOSS',
  BE: 'BE',
};

const formatTime = (timestamp: number) =>
  new Date(timestamp).toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });

const mapStrategy = (strategy: ApiStrategy): Strategy => ({
  ...strategy,
  enabled: Boolean(strategy.enabled),
});

export default function App() {
  const [selectedInstrument, setSelectedInstrument] = useState('EURUSD');
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [candles, setCandles] = useState<CandlePoint[]>([]);
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [signalLogs, setSignalLogs] = useState<SignalLog[]>([]);
  const [prediction, setPrediction] = useState<PredictionData>();
  const [predictionLoading, setPredictionLoading] = useState(false);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'open' | 'closed'>('connecting');
  const [isRunning, setIsRunning] = useState(false);

  const strategiesRef = useRef<Strategy[]>([]);
  const priceRef = useRef<number | null>(null);
  const lastCloseRef = useRef<number | null>(null);
  const previousInstrumentRef = useRef(selectedInstrument);

  useEffect(() => {
    strategiesRef.current = strategies;
  }, [strategies]);

  useEffect(() => {
    priceRef.current = currentPrice;
  }, [currentPrice]);

  useEffect(() => {
    if (candles.length > 0) {
      lastCloseRef.current = candles[candles.length - 1].close;
    }
  }, [candles]);

  const formatSignal = useCallback(
    (signal: SignalResponse): SignalLog => {
      const timestamp = signal.time * 1000;
      const strategyName =
        strategiesRef.current.find((item) => item.id === signal.strategy)?.name ?? signal.strategy;

      return {
        id: signal.id,
        timestamp,
        time: formatTime(timestamp),
        instrument: signal.symbol,
        strategy: strategyName,
        side: signal.side,
        entry: signal.entry,
        stop: signal.sl ?? null,
        target: signal.tp ?? null,
        status: signal.result ? statusMap[signal.result] ?? 'ACTIVE' : 'ACTIVE',
        result: signal.result ? resultMap[signal.result] : undefined,
        pnl: signal.pnl ?? null,
      };
    },
    [],
  );

  useEffect(() => {
    const controller = new AbortController();

    fetchStrategies(controller.signal)
      .then((catalog) => setStrategies(catalog.map(mapStrategy)))
      .catch((error) => {
        if (controller.signal.aborted) return;
        console.error('Failed to load strategies', error);
        toast.error('Unable to load strategies');
      });

    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setCandles([]);
    setCurrentPrice(null);

    fetchCandles({ symbol: selectedInstrument, timeframe: TIMEFRAME, limit: CANDLE_LIMIT }, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        setCandles(data);
        if (data.length > 0) {
          setCurrentPrice(data[data.length - 1].close);
        }
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        console.error('Failed to load candles', error);
        toast.error('Unable to load candles');
      });

    return () => controller.abort();
  }, [selectedInstrument]);

  useEffect(() => {
    const controller = new AbortController();

    fetchSignals({ symbol: selectedInstrument }, controller.signal)
      .then((items) => {
        if (controller.signal.aborted) return;
        const mapped = items.map((signal) => formatSignal(signal)).sort((a, b) => b.timestamp - a.timestamp);
        setSignalLogs(mapped);
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        console.error('Failed to load signals', error);
        toast.error('Unable to load signals');
      });

    return () => controller.abort();
  }, [formatSignal, selectedInstrument]);

  useEffect(() => {
    const previousInstrument = previousInstrumentRef.current;
    if (previousInstrument === selectedInstrument) {
      return;
    }

    const activeStrategies = strategiesRef.current.filter((strategy) => strategy.enabled);
    if (activeStrategies.length > 0) {
      const migrateStrategies = async () => {
        try {
          await Promise.all(
            activeStrategies.map((strategy) =>
              disableStrategy({ id: strategy.id, symbol: previousInstrument, tf: TIMEFRAME }),
            ),
          );
          await Promise.all(
            activeStrategies.map((strategy) =>
              enableStrategy({ id: strategy.id, symbol: selectedInstrument, tf: TIMEFRAME, settings: {} }),
            ),
          );
          toast.info(`Strategies reconfigured for ${selectedInstrument}`);
        } catch (error) {
          console.error('Failed to migrate strategies', error);
          toast.error('Unable to reconfigure strategies for the new instrument');
        }
      };

      migrateStrategies();
    }

    previousInstrumentRef.current = selectedInstrument;
  }, [selectedInstrument]);

  useEffect(() => {
    const controller = new AbortController();
    setPredictionLoading(true);

    fetchPrediction({ symbol: selectedInstrument, timeframe: TIMEFRAME }, controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const reference = priceRef.current ?? lastCloseRef.current ?? null;
        const target = data.target ?? null;
        let direction: PredictionData['direction'] = 'NEUTRAL';

        if (target !== null && reference !== null) {
          if (target > reference) direction = 'BULLISH';
          else if (target < reference) direction = 'BEARISH';
          else direction = 'NEUTRAL';
        }

        const confidence = data.confidence ? Math.round(data.confidence * 100) : 0;
        setPrediction({ direction, confidence, targetPrice: target });
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        console.error('Failed to load prediction', error);
        toast.error('Unable to load prediction');
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setPredictionLoading(false);
        }
      });

    return () => controller.abort();
  }, [selectedInstrument]);

  useEffect(() => {
    setWsStatus('connecting');
    const disconnect = connectMarketStream({
      onOpen: () => setWsStatus('open'),
      onClose: () => setWsStatus('closed'),
      onError: (event) => {
        console.error('WebSocket error', event);
        setWsStatus('closed');
        toast.error('Market stream disconnected');
      },
      onMessage: (message: MarketMessage) => {
        switch (message.topic) {
          case 'price.tick': {
            if (message.data.symbol !== selectedInstrument) return;
            const mid = (message.data.bid + message.data.ask) / 2;
            setCurrentPrice(Number(mid.toFixed(5)));
            break;
          }
          case 'bar.update': {
            if (message.data.symbol !== selectedInstrument || message.data.tf !== TIMEFRAME) return;
            const bar = message.data.bar;
            const nextCandle: CandlePoint = {
              timestamp: bar.t * 1000,
              open: bar.o,
              high: bar.h,
              low: bar.l,
              close: bar.c,
              volume: bar.v ?? 0,
            };

            setCandles((prev) => {
              const idx = prev.findIndex((item) => item.timestamp === nextCandle.timestamp);
              if (idx >= 0) {
                const copy = [...prev];
                copy[idx] = nextCandle;
                return copy;
              }
              const updated = [...prev, nextCandle].sort((a, b) => a.timestamp - b.timestamp);
              return updated.slice(-CANDLE_LIMIT);
            });
            setCurrentPrice(nextCandle.close);
            break;
          }
          case 'signal.new': {
            if (message.data.symbol !== selectedInstrument) return;
            const log = formatSignal(message.data);
            setSignalLogs((prev) => {
              const exists = prev.some((item) => item.id === log.id);
              if (exists) return prev;
              return [log, ...prev].sort((a, b) => b.timestamp - a.timestamp);
            });
            toast.success(`${message.data.side} signal`, {
              description: `${log.strategy} · Entry ${log.entry.toFixed(5)}`,
            });
            break;
          }
          default:
            break;
        }
      },
    });

    return () => disconnect();
  }, [formatSignal, selectedInstrument]);

  const handleStrategyChange = useCallback((id: string, enabled: boolean) => {
    setStrategies((prev) => prev.map((strategy) => (strategy.id === id ? { ...strategy, enabled } : strategy)));
  }, []);

  const activeStrategies = strategies.filter((strategy) => strategy.enabled);

  const handleRunnerToggle = async () => {
    if (activeStrategies.length === 0) {
      toast.info('Select at least one strategy to run');
      setIsRunning(false);
      return;
    }

    try {
      if (isRunning) {
        await Promise.all(
          activeStrategies.map((strategy) =>
            disableStrategy({ id: strategy.id, symbol: selectedInstrument, tf: TIMEFRAME }),
          ),
        );
        setIsRunning(false);
        toast.success('Strategies disabled');
      } else {
        await Promise.all(
          activeStrategies.map((strategy) =>
            enableStrategy({ id: strategy.id, symbol: selectedInstrument, tf: TIMEFRAME, settings: {} }),
          ),
        );
        setIsRunning(true);
        toast.success('Strategies enabled');
      }
    } catch (error) {
      console.error('Failed to toggle strategies', error);
      toast.error('Unable to update strategies');
    }
  };

  const priceTargets: PriceTarget[] = useMemo(() => {
    return signalLogs
      .filter((log) => log.instrument === selectedInstrument)
      .flatMap((log) => {
        const targets: PriceTarget[] = [];
        targets.push({ id: `${log.id}-entry`, price: log.entry, type: 'entry', strategy: log.strategy });
        if (log.stop !== undefined && log.stop !== null) {
          targets.push({ id: `${log.id}-stop`, price: log.stop, type: 'stop', strategy: log.strategy });
        }
        if (log.target !== undefined && log.target !== null) {
          targets.push({ id: `${log.id}-target`, price: log.target, type: 'target', strategy: log.strategy });
        }
        return targets;
      });
  }, [selectedInstrument, signalLogs]);

  return (
    <div className="w-full min-h-screen bg-background">
      <Toaster richColors position="top-right" />
      <div className="flex flex-col gap-4 p-4 max-w-[1800px] mx-auto w-full">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary" />
            <h1 className="text-foreground">Forex Strategy Runner</h1>
          </div>
          <div className="flex items-center gap-4">
            <InstrumentSelector value={selectedInstrument} onChange={setSelectedInstrument} />
            <Button
              variant={isRunning ? 'destructive' : 'default'}
              onClick={handleRunnerToggle}
              className="gap-2"
            >
              {isRunning ? (
                <>
                  <PauseCircle className="h-4 w-4" />
                  Stop
                </>
              ) : (
                <>
                  <PlayCircle className="h-4 w-4" />
                  Start
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-4">
          <div className="lg:col-span-1">
            <StrategySelector
              strategies={strategies}
              symbol={selectedInstrument}
              onStrategyChange={handleStrategyChange}
            />
          </div>
          <div className="lg:col-span-3 flex flex-col gap-4">
            <div className="bg-card border border-border rounded-lg p-4 h-[500px]">
              <ForexChart
                instrument={selectedInstrument}
                candles={candles}
                currentPrice={currentPrice}
                connectionStatus={wsStatus}
                priceTargets={priceTargets}
              />
            </div>
            <PredictionPanel prediction={prediction} timeframe="Next 1-4 hours" loading={predictionLoading} />
          </div>
        </div>

        <div className="min-h-[350px]">
          <SignalLogs logs={signalLogs.filter((log) => log.instrument === selectedInstrument)} />
        </div>
      </div>
    </div>
  );
}
