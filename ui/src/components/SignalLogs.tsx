import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ArrowUp, ArrowDown } from 'lucide-react';

export interface SignalLog {
  id: string;
  /** Backend may send epoch seconds; UI may hold a string */
  time: number | string;
  /** Prefer instrument or symbol if present from backend */
  instrument?: string;
  symbol?: string;

  strategy: string;
  side: 'BUY' | 'SELL';

  /** UI alias of backend fields */
  entry: number;
  stop?: number | null;   // backend: sl
  target?: number | null; // backend: tp

  /** Old UI status is optional; backend uses `result` */
  status?: 'ACTIVE' | 'CLOSED' | 'STOPPED';
  result?: 'WIN' | 'LOSS' | 'BE' | 'OPEN';
  pnl?: number | null;
}

interface SignalLogsProps {
  logs: SignalLog[];
}

/** Format price with FX-friendly precision by symbol */
function fmtPrice(value: number | null | undefined, sym?: string) {
  if (value === null || value === undefined) return '-';
  const symbol = sym || '';
  // crude heuristic: JPY pairs -> 3 dp, else 5 dp
  const dp = /JPY$/.test(symbol) ? 3 : 5;
  return value.toFixed(dp);
}

/** Accepts epoch seconds or a ready string */
function fmtTime(t: number | string) {
  if (typeof t === 'number') {
    const d = new Date(t * 1000);
    return d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
  return t;
}

export function SignalLogs({ logs }: SignalLogsProps) {
  const deriveStatusFromResult = (result?: SignalLog['result']): 'ACTIVE' | 'CLOSED' | 'STOPPED' | 'BE' => {
    switch (result) {
      case 'OPEN': return 'ACTIVE';
      case 'WIN':  return 'CLOSED';
      case 'LOSS': return 'STOPPED';
      case 'BE':   return 'BE';
      default:     return 'ACTIVE';
    }
  };

  const getStatusColor = (status: 'ACTIVE' | 'CLOSED' | 'STOPPED' | 'BE'): 'default' | 'secondary' | 'destructive' => {
    switch (status) {
      case 'ACTIVE': return 'default';
      case 'CLOSED': return 'secondary';
      case 'BE':     return 'secondary';
      case 'STOPPED':return 'destructive';
    }
  };

  const getResultColor = (result?: SignalLog['result']): 'default' | 'secondary' | 'destructive' => {
    if (result === 'WIN') return 'default';
    if (result === 'LOSS') return 'destructive';
    return 'secondary'; // OPEN or BE
  };

  const totalPnl = logs.reduce((sum, log) => sum + (log.pnl || 0), 0);
  const winCount  = logs.filter((l) => l.result === 'WIN').length;
  const lossCount = logs.filter((l) => l.result === 'LOSS').length;
  const winRate = winCount + lossCount > 0 ? ((winCount / (winCount + lossCount)) * 100).toFixed(1) : '0';

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-2">
        <CardTitle>Signal Logs</CardTitle>
        <CardDescription>Live strategy signals</CardDescription>
      </CardHeader>

      <CardContent className="flex-1 overflow-hidden p-0">
        {/* summary row */}
        <div className="px-4 pb-3">
          <div className="flex items-center gap-4 text-sm">
            <span>
              Total P&amp;L:{' '}
              <span className={totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                ${totalPnl.toFixed(2)}
              </span>
            </span>
            <span>Win Rate: {winRate}%</span>
            <span>Signals: {logs.length}</span>
          </div>
        </div>

        <ScrollArea className="h-full">
          <Table>
            <TableHeader className="sticky top-0 bg-card z-10">
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Instrument</TableHead>
                <TableHead>Strategy</TableHead>
                <TableHead>Side</TableHead>
                <TableHead>Entry</TableHead>
                <TableHead>Stop</TableHead>
                <TableHead>Target</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Result</TableHead>
                <TableHead className="text-right">P&amp;L</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center text-muted-foreground py-8">
                    No signals yet. Enable strategies and wait for signals…
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => {
                  const symbol = log.instrument || log.symbol;
                  const status = log.status ?? deriveStatusFromResult(log.result);
                  return (
                    <TableRow key={log.id}>
                      <TableCell className="text-muted-foreground">{fmtTime(log.time)}</TableCell>
                      <TableCell>{symbol ?? '-'}</TableCell>
                      <TableCell>{log.strategy}</TableCell>

                      <TableCell>
                        <Badge
                          variant={log.side === 'BUY' ? 'default' : 'destructive'}
                          className="flex items-center gap-1 w-fit"
                        >
                          {log.side === 'BUY' ? (
                            <ArrowUp className="w-3 h-3" />
                          ) : (
                            <ArrowDown className="w-3 h-3" />
                          )}
                          {log.side}
                        </Badge>
                      </TableCell>

                      <TableCell>{fmtPrice(log.entry, symbol)}</TableCell>
                      <TableCell>{fmtPrice(log.stop ?? null, symbol)}</TableCell>
                      <TableCell>{fmtPrice(log.target ?? null, symbol)}</TableCell>

                      <TableCell>
                        <Badge variant={getStatusColor(status)}>{status}</Badge>
                      </TableCell>

                      <TableCell>
                        {log.result && <Badge variant={getResultColor(log.result)}>{log.result}</Badge>}
                      </TableCell>

                      <TableCell
                        className={`text-right ${
                          log.pnl !== null && log.pnl !== undefined
                            ? log.pnl >= 0
                              ? 'text-green-500'
                              : 'text-red-500'
                            : ''
                        }`}
                      >
                        {log.pnl !== null && log.pnl !== undefined ? `$${log.pnl.toFixed(2)}` : '-'}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
