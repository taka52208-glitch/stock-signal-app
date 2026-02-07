import { Card, CardContent, Typography, Box, CircularProgress } from '@mui/material';
import type { BrokerageBalance } from '../types';

interface Props {
  balance: BrokerageBalance | undefined;
  isLoading: boolean;
}

export default function AccountBalanceCard({ balance, isLoading }: Props) {
  if (isLoading) {
    return (
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="center" py={2}>
            <CircularProgress size={24} />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (!balance) return null;

  return (
    <Card sx={{ mb: 2, bgcolor: 'primary.main', color: 'white' }}>
      <CardContent>
        <Typography variant="body2" sx={{ opacity: 0.8 }}>
          口座残高
        </Typography>
        <Typography variant="h4" fontWeight="bold">
          ¥{balance.totalValue.toLocaleString()}
        </Typography>
        <Box display="flex" gap={3} mt={1}>
          <Box>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>現物</Typography>
            <Typography variant="body2">¥{balance.cashBalance.toLocaleString()}</Typography>
          </Box>
          <Box>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>信用</Typography>
            <Typography variant="body2">¥{balance.marginBalance.toLocaleString()}</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
