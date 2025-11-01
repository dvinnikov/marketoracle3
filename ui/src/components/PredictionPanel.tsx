import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export interface PredictionData {
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;
  targetPrice?: number | null;
}

interface PredictionPanelProps {
  prediction?: PredictionData;
  timeframe: string;
  loading?: boolean;
}

export function PredictionPanel({ prediction, timeframe, loading }: PredictionPanelProps) {
  const direction = prediction?.direction ?? 'NEUTRAL';
  const confidence = prediction?.confidence ?? 0;
  const targetPrice = prediction?.targetPrice ?? null;

  const getPredictionColor = () => {
    switch (direction) {
      case 'BULLISH':
        return 'text-green-500';
      case 'BEARISH':
        return 'text-red-500';
      default:
        return 'text-muted-foreground';
    }
  };

  const getPredictionIcon = () => {
    switch (direction) {
      case 'BULLISH':
        return <TrendingUp className="h-6 w-6" />;
      case 'BEARISH':
        return <TrendingDown className="h-6 w-6" />;
      default:
        return <Minus className="h-6 w-6" />;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Market Prediction</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>Fetching prediction…</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={getPredictionColor()}>{getPredictionIcon()}</div>
                <div>
                  <p className={getPredictionColor()}>{direction}</p>
                  <p className="text-sm text-muted-foreground">{timeframe}</p>
                </div>
              </div>
              <Badge variant={confidence >= 70 ? 'default' : 'secondary'}>
                {confidence}% Confidence
              </Badge>
            </div>

            {targetPrice !== null ? (
              <div className="flex items-center justify-between border-t border-border pt-3">
                <span className="text-muted-foreground">Target Price</span>
                <span className="text-foreground">{targetPrice.toFixed(5)}</span>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No target available yet.</p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
