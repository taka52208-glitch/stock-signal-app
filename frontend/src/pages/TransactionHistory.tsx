import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Delete } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { Transaction } from '../types';

export default function TransactionHistory() {
  const queryClient = useQueryClient();

  const { data: transactions, isLoading, error } = useQuery({
    queryKey: ['transactions'],
    queryFn: api.getTransactions,
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
    },
  });

  const handleDelete = (id: number) => {
    if (confirm('この取引記録を削除しますか？')) {
      deleteMutation.mutate(id);
    }
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={2}>
        <Alert severity="error">データの取得に失敗しました</Alert>
      </Box>
    );
  }

  return (
    <Box p={2}>
      <Typography variant="h5" fontWeight="bold" mb={2}>
        取引履歴
      </Typography>

      {transactions?.length === 0 ? (
        <Alert severity="info">取引履歴がありません。</Alert>
      ) : (
        transactions?.map((transaction: Transaction) => (
          <Card key={transaction.id} sx={{ mb: 1 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box flex={1}>
                  <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                    <Chip
                      label={transaction.transactionType === 'buy' ? '買' : '売'}
                      size="small"
                      color={transaction.transactionType === 'buy' ? 'success' : 'error'}
                    />
                    <Typography variant="subtitle2" color="text.secondary">
                      {transaction.code}
                    </Typography>
                  </Box>
                  <Typography variant="body1" fontWeight="bold">
                    {transaction.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {transaction.quantity}株 × ¥{transaction.price.toLocaleString()}
                  </Typography>
                  {transaction.memo && (
                    <Typography variant="caption" color="text.secondary">
                      {transaction.memo}
                    </Typography>
                  )}
                </Box>
                <Box textAlign="right">
                  <Typography variant="body1" fontWeight="bold">
                    ¥{transaction.totalAmount.toLocaleString()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {formatDate(transaction.transactionDate)}
                  </Typography>
                </Box>
                <IconButton
                  size="small"
                  onClick={() => handleDelete(transaction.id)}
                  disabled={deleteMutation.isPending}
                  sx={{ ml: 1 }}
                >
                  <Delete fontSize="small" />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        ))
      )}
    </Box>
  );
}
