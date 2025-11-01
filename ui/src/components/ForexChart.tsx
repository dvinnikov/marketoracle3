import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import type { CandlePoint } from '../lib/api';
import { Badge } from './ui/badge';

export interface PriceTarget {
  id: string;
  price: number;
  type: 'entry' | 'stop' | 'target';
  strategy: string;
}

interface ForexChartProps {
  instrument: string;
  candles: CandlePoint[];
  currentPrice: number | null;
  connectionStatus: 'connecting' | 'open' | 'closed';
  priceTargets: PriceTarget[];
}

const formatTimestamp = (timestamp: number) =>
  new Date(timestamp).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });

export function ForexChart({ instrument, candles, currentPrice, connectionStatus, priceTargets }: ForexChartProps) {
  const chartData = useMemo(() => {
    return candles.map((candle) => ({
      ...candle,
      time: formatTimestamp(candle.timestamp),
      price: candle.close,
    }));
  }, [candles]);

  const priceDelta = useMemo(() => {
    if (chartData.length < 2) return 0;
    const prev = chartData[chartData.length - 2].price;
    const last = chartData[chartData.length - 1].price;
    return last - prev;
  }, [chartData]);

  const statusLabel = connectionStatus === 'open'
    ? 'Live'
    : connectionStatus === 'connecting'
      ? 'Connecting…'
      : 'Disconnected';

  const statusColor = connectionStatus === 'open'
    ? 'text-green-500'
    : connectionStatus === 'connecting'
      ? 'text-amber-500'
      : 'text-red-500';

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-muted-foreground">{payload[0].payload.time}</p>
          <p className="text-foreground">{payload[0].value.toFixed(5)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="h-full w-full flex flex-col">
      <div className="flex items-center justify-between mb-4 px-4">
        <div className="flex items-center gap-4">
          <h2 className="text-foreground">{instrument}</h2>
          <div className="flex items-center gap-2">
            <span className="text-foreground">{currentPrice !== null ? currentPrice.toFixed(5) : '—'}</span>
            {chartData.length > 0 && (
              <Badge variant={priceDelta >= 0 ? 'default' : 'destructive'}>
                {priceDelta.toFixed(5)}
              </Badge>
            )}
          </div>
        </div>
        <span className={`text-sm ${statusColor}`}>{statusLabel}</span>
      </div>

      <div className="flex-1 relative">
        {chartData.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center text-muted-foreground text-sm">
            Awaiting data…
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="time"
                stroke="var(--muted-foreground)"
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={['auto', 'auto']}
                stroke="var(--muted-foreground)"
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => value.toFixed(5)}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="price"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />

              {priceTargets.map((target) => (
                <ReferenceLine
                  key={target.id}
                  y={target.price}
                  stroke={
                    target.type === 'entry'
                      ? 'hsl(var(--chart-2))'
                      : target.type === 'stop'
                        ? 'hsl(var(--destructive))'
                        : 'hsl(var(--chart-4))'
                  }
                  strokeDasharray="5 5"
                  strokeWidth={2}
                  label={{
                    value: `${target.type.toUpperCase()}: ${target.price.toFixed(5)}`,
                    position: 'right',
                    fill: 'var(--foreground)',
                    fontSize: 11,
                  }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        )}

        {priceTargets.length > 0 && (
          <div className="absolute top-2 right-2 bg-card/90 backdrop-blur border border-border rounded-lg p-2 space-y-1">
            {priceTargets.map((target) => (
              <div key={target.id} className="flex items-center gap-2 text-xs">
                <div
                  className="w-3 h-3 rounded-sm"
                  style={{
                    backgroundColor:
                      target.type === 'entry'
                        ? 'hsl(var(--chart-2))'
                        : target.type === 'stop'
                          ? 'hsl(var(--destructive))'
                          : 'hsl(var(--chart-4))',
                  }}
                />
                <span className="text-muted-foreground">{target.strategy} · {target.type}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
