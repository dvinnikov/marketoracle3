import { useEffect, useMemo, useState } from 'react';
import { TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { fetchInstruments, formatInstrumentLabel, type Instrument } from '../lib/api';

interface InstrumentSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export function InstrumentSelector({ value, onChange }: InstrumentSelectorProps) {
  const [instruments, setInstruments] = useState<Instrument[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    fetchInstruments(controller.signal)
      .then((items) => {
        setInstruments(items);
        if (items.length > 0) {
          const current = items.find((item) => item.symbol === value);
          if (!current) {
            onChange(items[0].symbol);
          }
        }
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        console.error('Failed to load instruments', error);
        toast.error('Unable to load instruments');
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [onChange, value]);

  const options = useMemo(() => {
    return instruments.map((instrument) => {
      const { label, name } = formatInstrumentLabel(instrument);
      return { value: instrument.symbol, label, name };
    });
  }, [instruments]);

  return (
    <div className="flex items-center gap-2">
      <TrendingUp className="w-5 h-5 text-muted-foreground" />
      <Select value={value} onValueChange={onChange} disabled={loading || options.length === 0}>
        <SelectTrigger className="w-[280px]">
          <SelectValue placeholder={loading ? 'Loading instruments…' : 'Select instrument'} />
        </SelectTrigger>
        <SelectContent>
          {options.map((instrument) => (
            <SelectItem key={instrument.value} value={instrument.value}>
              <div className="flex flex-col items-start">
                <span>{instrument.label}</span>
                <span className="text-xs text-muted-foreground">{instrument.name}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
