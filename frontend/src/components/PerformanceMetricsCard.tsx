import { Card, CardContent, Typography, Box } from '@mui/material';

interface Props {
  summary: Record<string, unknown>;
  initialCapital: number;
}

export default function PerformanceMetricsCard({ summary, initialCapital }: Props) {
  const metrics = [
    {
      label: '最終資産',
      value: `¥${(summary.finalValue as number || 0).toLocaleString()}`,
      color: 'text.primary',
    },
    {
      label: '総リターン',
      value: `${(summary.totalReturn as number || 0) >= 0 ? '+' : ''}¥${(summary.totalReturn as number || 0).toLocaleString()}`,
      sub: `(${(summary.totalReturnPercent as number || 0) >= 0 ? '+' : ''}${(summary.totalReturnPercent as number || 0).toFixed(2)}%)`,
      color: (summary.totalReturn as number || 0) >= 0 ? 'success.main' : 'error.main',
    },
    {
      label: '最大ドローダウン',
      value: `-${(summary.maxDrawdown as number || 0).toFixed(2)}%`,
      color: 'error.main',
    },
    {
      label: '勝率',
      value: `${(summary.winRate as number || 0).toFixed(1)}%`,
      color: (summary.winRate as number || 0) >= 50 ? 'success.main' : 'warning.main',
    },
    {
      label: '取引回数',
      value: `${summary.totalTrades || 0}回`,
      color: 'text.primary',
    },
    {
      label: 'プロフィットファクター',
      value: `${(summary.profitFactor as number || 0).toFixed(2)}`,
      color: (summary.profitFactor as number || 0) >= 1 ? 'success.main' : 'error.main',
    },
    {
      label: 'シャープレシオ',
      value: `${(summary.sharpeRatio as number || 0).toFixed(2)}`,
      color: (summary.sharpeRatio as number || 0) >= 1 ? 'success.main' : 'warning.main',
    },
  ];

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" fontWeight="bold" mb={2}>
          パフォーマンス指標
        </Typography>
        <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
          {metrics.map((m, i) => (
            <Box key={i}>
              <Typography variant="caption" color="text.secondary">
                {m.label}
              </Typography>
              <Typography variant="h6" fontWeight="bold" color={m.color}>
                {m.value}
              </Typography>
              {m.sub && (
                <Typography variant="caption" color={m.color}>
                  {m.sub}
                </Typography>
              )}
            </Box>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
}
