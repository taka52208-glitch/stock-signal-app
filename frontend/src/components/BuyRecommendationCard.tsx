import { useNavigate } from 'react-router-dom';
import { Box, Card, CardContent, Typography, Chip, Button } from '@mui/material';
import { TrendingUp } from '@mui/icons-material';
import type { Recommendation } from '../types';
import SignalStrengthDisplay from './SignalStrengthDisplay';

const SIGNAL_LABEL: Record<string, string> = {
  RSI: 'RSI売られすぎ',
  MACD: 'MACDクロス',
  GoldenCross: 'ゴールデンクロス',
};

interface Props {
  recommendation: Recommendation;
}

export default function BuyRecommendationCard({ recommendation: rec }: Props) {
  const navigate = useNavigate();

  return (
    <Card sx={{ mb: 1.5, border: '1px solid', borderColor: 'success.light' }}>
      <CardContent sx={{ pb: '12px !important' }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
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

        <Box display="flex" gap={0.5} mb={1.5} flexWrap="wrap">
          {rec.activeSignals.map((s) => (
            <Chip
              key={s}
              label={SIGNAL_LABEL[s] || s}
              size="small"
              color="success"
              variant="outlined"
              icon={<TrendingUp />}
            />
          ))}
        </Box>

        {rec.suggestedQuantity != null && rec.suggestedQuantity > 0 && (
          <Box sx={{ bgcolor: 'success.50', bgcolor2: '#e8f5e9', p: 1.5, borderRadius: 1, mb: 1.5 }}
            style={{ backgroundColor: '#e8f5e9' }}>
            <Typography variant="caption" color="text.secondary">購入提案</Typography>
            <Typography variant="body1" fontWeight="bold">
              {rec.suggestedQuantity}株 × ¥{rec.currentPrice.toLocaleString()} = ¥{rec.suggestedAmount?.toLocaleString()}
            </Typography>
          </Box>
        )}

        <Box display="grid" gridTemplateColumns="1fr 1fr 1fr" gap={1} mb={1.5}>
          {rec.targetPrice != null && (
            <Box>
              <Typography variant="caption" color="text.secondary">目標価格</Typography>
              <Typography variant="body2" fontWeight="bold" color="success.main">
                ¥{rec.targetPrice.toLocaleString()}
              </Typography>
            </Box>
          )}
          {rec.expectedProfit != null && (
            <Box>
              <Typography variant="caption" color="text.secondary">期待利益</Typography>
              <Typography variant="body2" fontWeight="bold" color="success.main">
                +¥{rec.expectedProfit.toLocaleString()}
                {rec.expectedProfitPercent != null && ` (${rec.expectedProfitPercent}%)`}
              </Typography>
            </Box>
          )}
          {rec.stopLossPrice != null && (
            <Box>
              <Typography variant="caption" color="text.secondary">損切りライン</Typography>
              <Typography variant="body2" fontWeight="bold" color="error.main">
                ¥{rec.stopLossPrice.toLocaleString()}
              </Typography>
            </Box>
          )}
        </Box>

        <Button
          size="small"
          variant="text"
          onClick={() => navigate(`/stock/${rec.code}`)}
          sx={{ mr: 1 }}
        >
          詳細を見る
        </Button>
      </CardContent>
    </Card>
  );
}
