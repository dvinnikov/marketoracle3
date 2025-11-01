import type { KeyboardEvent, MouseEvent } from 'react';
import { Checkbox } from './ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';
import { disableStrategy, enableStrategy, type Strategy as ApiStrategy } from '../lib/api';

export interface Strategy extends ApiStrategy {
  enabled: boolean;
  winRate?: number;
}

interface StrategySelectorProps {
  strategies: Strategy[];
  symbol: string;
  onStrategyChange: (id: string, enabled: boolean) => void;
}

const TIMEFRAME = 60;

export function StrategySelector({ strategies, symbol, onStrategyChange }: StrategySelectorProps) {
  const activeCount = strategies.filter((strategy) => strategy.enabled).length;

  const handleToggle = async (strategy: Strategy) => {
    const nextEnabled = !strategy.enabled;
    onStrategyChange(strategy.id, nextEnabled);

    try {
      if (nextEnabled) {
        await enableStrategy({ id: strategy.id, symbol, tf: TIMEFRAME, settings: {} });
      } else {
        await disableStrategy({ id: strategy.id, symbol, tf: TIMEFRAME });
      }
    } catch (error) {
      console.error('Failed to toggle strategy', error);
      onStrategyChange(strategy.id, strategy.enabled);
      toast.error(`Failed to ${nextEnabled ? 'enable' : 'disable'} ${strategy.name}`);
    }
  };

  return (
    <Card className="h-full flex flex-col">
      <CardHeader>
        <CardTitle>Trading Strategies</CardTitle>
        <CardDescription>
          Select strategies to run ({activeCount} active)
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden">
        <ScrollArea className="h-full pr-4">
          <div className="space-y-3">
            {strategies.map((strategy) => {
              const badgeLabel = strategy.winRate ? `${strategy.winRate}% WR` : 'Ready';
              const badgeVariant = strategy.winRate && strategy.winRate >= 60 ? 'default' : 'secondary';

              const onToggle = () => handleToggle(strategy);

              return (
                <div
                  key={strategy.id}
                  role="button"
                  tabIndex={0}
                  onClick={onToggle}
                  onKeyDown={(event: KeyboardEvent<HTMLDivElement>) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      onToggle();
                    }
                  }}
                  className="flex w-full items-start space-x-3 rounded-lg border border-border bg-card p-3 text-left transition-colors hover:bg-accent/50 focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <Checkbox
                    checked={strategy.enabled}
                    onCheckedChange={() => onToggle()}
                    onClick={(event: MouseEvent<HTMLButtonElement>) => event.stopPropagation()}
                    className="mt-1"
                  />
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between">
                      <p className="text-foreground">{strategy.name}</p>
                      <Badge variant={badgeVariant}>{badgeLabel}</Badge>
                    </div>
                    <p className="text-muted-foreground text-sm">{strategy.description || 'No description available.'}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
