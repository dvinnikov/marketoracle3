import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { ArrowUp, ArrowDown } from 'lucide-react';

export interface SignalLog {
  id: string;
  timestamp: number;
  time: string;
  instrument: string;
  strategy: string;
  side: 'BUY' | 'SELL';
  entry: number;
  stop?: number | null;
  target?: number | null;
  status: 'ACTIVE' | 'CLOSED' | 'STOPPED' | 'BE';
  result?: 'WIN' | 'LOSS' | 'BE';
  pnl?: number | null;
}

interface SignalLogsProps {
  logs: SignalLog[];
}

export function SignalLogs({ logs }: SignalLogsProps) {
  const getStatusColor = (status: SignalLog['status']) => {
    switch (status) {
      case 'ACTIVE':
        return 'default';
      case 'CLOSED':
        return 'secondary';
      case 'STOPPED':
        return 'destructive';
      case 'BE':
        return 'secondary';
      default:
        return 'secondary';
    }
  };

  const getResultColor = (result?: SignalLog['result']) => {
    if (result === 'WIN') return 'default';
    if (result === 'LOSS') return 'destructive';
    if (result === 'BE') return 'secondary';
    return 'secondary';
  };

  const totalPnl = logs.reduce((sum, log) => sum + (log.pnl ?? 0), 0);
  const decisive = logs.filter((log) => log.result === 'WIN' || log.result === 'LOSS');
  const winCount = decisive.filter((log) => log.result === 'WIN').length;
  const winRate = decisive.length > 0 ? ((winCount / decisive.length) * 100).toFixed(1) : '0.0';

  return (
    <Card className="flex h-full flex-col">
      <CardHeader>
        <CardTitle>Signal Logs</CardTitle>
        <CardDescription>Live and historical trade signals</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-0">
        <div className="flex flex-wrap items-center gap-4 border-b border-border px-4 py-3 text-sm text-muted-foreground">
          <span>
            Total P&amp;L:{' '}
            <span className={totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}>
              ${totalPnl.toFixed(2)}
            </span>
          </span>
          <span>Win Rate: {winRate}%</span>
          <span>Signals: {logs.length}</span>
        </div>
        <ScrollArea className="h-full">
          <Table>
            <TableHeader className="sticky top-0 z-10 bg-card">
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
                  <TableCell colSpan={10} className="py-8 text-center text-muted-foreground">
                    No signals yet. Select strategies to begin.
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-muted-foreground">{log.time}</TableCell>
                    <TableCell>{log.instrument}</TableCell>
                    <TableCell>{log.strategy}</TableCell>
                    <TableCell>
                      <Badge variant={log.side === 'BUY' ? 'default' : 'destructive'} className="flex w-fit items-center gap-1">
                        {log.side === 'BUY' ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />}
                        {log.side}
                      </Badge>
                    </TableCell>
                    <TableCell>{log.entry.toFixed(5)}</TableCell>
                    <TableCell>{log.stop !== undefined && log.stop !== null ? log.stop.toFixed(5) : '—'}</TableCell>
                    <TableCell>{log.target !== undefined && log.target !== null ? log.target.toFixed(5) : '—'}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusColor(log.status)}>{log.status}</Badge>
                    </TableCell>
                    <TableCell>
                      {log.result && (
                        <Badge variant={getResultColor(log.result)}>{log.result}</Badge>
                      )}
                    </TableCell>
                    <TableCell className={`text-right ${log.pnl ? (log.pnl >= 0 ? 'text-green-500' : 'text-red-500') : ''}`}>
                      {log.pnl !== undefined && log.pnl !== null ? `$${log.pnl.toFixed(2)}` : '—'}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
