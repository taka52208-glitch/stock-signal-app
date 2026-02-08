import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, IconButton, Card, CardContent, Chip, Fab,
  CircularProgress, Alert,
} from '@mui/material';
import { ArrowBack, Add, Cancel } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import AccountBalanceCard from '../components/AccountBalanceCard';
import OrderDialog from '../components/OrderDialog';

const statusLabels: Record<string, string> = {
  pending: '待機中',
  submitted: '発注済',
  filled: '約定',
  cancelled: 'キャンセル',
  failed: '失敗',
};

const statusColors: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
  pending: 'default',
  submitted: 'info',
  filled: 'success',
  cancelled: 'warning',
  failed: 'error',
};

export default function BrokerageOrders() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [orderDialogOpen, setOrderDialogOpen] = useState(false);

  const { data: orders, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: api.getOrders,
  });

  const { data: balance, isLoading: balanceLoading } = useQuery({
    queryKey: ['brokerageBalance'],
    queryFn: api.getBrokerageBalance,
    retry: false,
  });

  const cancelMutation = useMutation({
    mutationFn: api.cancelOrder,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={2}>
      <Box display="flex" alignItems="center" mb={2}>
        <IconButton onClick={() => navigate(-1)}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h6" fontWeight="bold" ml={1}>
          注文管理
        </Typography>
      </Box>

      <AccountBalanceCard balance={balance} isLoading={balanceLoading} />

      {orders?.length === 0 ? (
        <Alert severity="info">
          注文履歴がありません。右下の＋ボタンから注文できます。
        </Alert>
      ) : (
        orders?.map((order) => (
          <Card key={order.id} sx={{ mb: 1 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                    <Typography variant="body1" fontWeight="bold">
                      {order.code}
                    </Typography>
                    <Chip
                      label={order.side === 'buy' ? '買' : '売'}
                      size="small"
                      color={order.side === 'buy' ? 'success' : 'error'}
                    />
                    <Chip
                      label={order.orderType === 'market' ? '成行' : order.orderType === 'limit' ? '指値' : '逆指値'}
                      size="small"
                      variant="outlined"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {order.quantity}株
                    {order.price != null ? ` × ¥${order.price.toLocaleString()}` : ''}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(order.createdAt).toLocaleString('ja-JP')}
                  </Typography>
                </Box>
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    label={statusLabels[order.status] || order.status}
                    size="small"
                    color={statusColors[order.status] || 'default'}
                  />
                  {(order.status === 'pending' || order.status === 'submitted') && (
                    <IconButton
                      size="small"
                      onClick={() => cancelMutation.mutate(order.id)}
                    >
                      <Cancel fontSize="small" />
                    </IconButton>
                  )}
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))
      )}

      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 72, right: 16 }}
        onClick={() => setOrderDialogOpen(true)}
      >
        <Add />
      </Fab>

      <OrderDialog
        open={orderDialogOpen}
        onClose={() => setOrderDialogOpen(false)}
      />
    </Box>
  );
}
