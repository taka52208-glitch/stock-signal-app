import { Card, CardContent, Typography } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import type { BacktestSnapshot } from '../types';

interface Props {
  snapshots: BacktestSnapshot[];
  initialCapital: number;
}

export default function EquityCurveChart({ snapshots, initialCapital }: Props) {
  if (!snapshots.length) return null;

  const data = snapshots.map((s) => ({
    date: s.date.slice(5), // MM-DD
    portfolioValue: s.portfolioValue,
    cash: s.cash,
  }));

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" fontWeight="bold" mb={2}>
          資産推移
        </Typography>
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fontSize: 10 }}
              tickFormatter={(v) => `¥${(v / 10000).toFixed(0)}万`}
            />
            <Tooltip
              formatter={(value: number) => [`¥${value.toLocaleString()}`, '']}
              labelFormatter={(label) => `日付: ${label}`}
            />
            <Legend />
            <Line type="monotone" dataKey="portfolioValue" stroke="#1976d2" name="総資産" dot={false} />
            <Line type="monotone" dataKey="cash" stroke="#4caf50" name="現金" dot={false} strokeDasharray="5 5" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
