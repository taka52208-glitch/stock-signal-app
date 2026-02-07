import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

interface Props {
  code: string;
}

const typeColor = (type: string): 'success' | 'error' | 'warning' | 'info' => {
  switch (type) {
    case 'limit_buy': return 'success';
    case 'stop_loss': return 'error';
    case 'take_profit': return 'info';
    case 'trailing_stop': return 'warning';
    default: return 'info';
  }
};

export default function PriceSuggestionCard({ code }: Props) {
  const { data } = useQuery({
    queryKey: ['priceSuggestions', code],
    queryFn: () => api.getSuggestedPrices(code),
    enabled: !!code,
  });

  if (!data || data.suggestions.length === 0) return null;

  return (
    <Card sx={{ mb: 2 }}>
      <CardContent>
        <Typography variant="subtitle1" fontWeight="bold" mb={2}>
          注文価格の提案
        </Typography>
        {data.suggestions.map((s, i) => (
          <Box key={i} display="flex" alignItems="center" justifyContent="space-between" mb={1.5}
            sx={{ pb: 1, borderBottom: i < data.suggestions.length - 1 ? '1px solid' : 'none', borderColor: 'divider' }}
          >
            <Box>
              <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                <Chip label={s.label} size="small" color={typeColor(s.type)} variant="outlined" />
              </Box>
              <Typography variant="caption" color="text.secondary">
                {s.reason}
              </Typography>
            </Box>
            <Typography variant="h6" fontWeight="bold">
              ¥{s.price.toLocaleString()}
            </Typography>
          </Box>
        ))}
      </CardContent>
    </Card>
  );
}
