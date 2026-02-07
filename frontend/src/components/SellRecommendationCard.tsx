import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, Chip, Button } from '@mui/material';
import { TrendingDown } from '@mui/icons-material';
import type { Recommendation } from '../types';
import SignalStrengthDisplay from './SignalStrengthDisplay';

const SIGNAL_LABEL: Record<string, string> = {
  RSI: 'RSI買われすぎ',
  MACD: 'MACDクロス',
  DeadCross: 'デッドクロス',
};

interface Props {
  recommendation: Recommendation;
}

export default function SellRecommendationCard({ recommendation: rec }: Props) {
  const navigate = useNavigate();

  return (
    <Card sx={{ mb: 1.5, border: '1px solid', borderColor: 'error.light' }}>
      <CardContent sx={{ pb: '12px !important' }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography variant="caption" color="text.secondary">{rec.code}</Typography>
            <Typography variant="subtitle1" fontWeight="bold">{rec.name}</Typography>
          </Box>
          <Box textAlign="right">
            <Typography variant="h6" fontWeight="bold">
              ¥{rec.currentPrice.toLocaleString()}
            </Typography>
            <SignalStrengthDisplay strength={rec.signalStrength} />
          </Box>
        </Box>

        <Box display="flex" gap={0.5} mt={1} mb={1} flexWrap="wrap">
          {rec.activeSignals.map((s) => (
            <Chip
              key={s}
              label={SIGNAL_LABEL[s] || s}
              size="small"
              color="error"
              variant="outlined"
              icon={<TrendingDown />}
            />
          ))}
        </Box>

        <Button
          size="small"
          variant="text"
          onClick={() => navigate(`/stock/${rec.code}`)}
        >
          詳細を見る
        </Button>
      </CardContent>
    </Card>
  );
}
