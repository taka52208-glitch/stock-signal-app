import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, IconButton, Card, CardContent, Fab, Chip,
  CircularProgress, Alert, Checkbox,  Button,
} from '@mui/material';
import { ArrowBack, Add, Delete, CompareArrows } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import BacktestCompareDialog from '../components/BacktestCompareDialog';

export default function BacktestList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [compareOpen, setCompareOpen] = useState(false);

  const { data: backtests, isLoading } = useQuery({
    queryKey: ['backtests'],
    queryFn: api.getBacktests,
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteBacktest,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['backtests'] }),
  });

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box p={2}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
        <Box display="flex" alignItems="center">
          <IconButton onClick={() => navigate(-1)}>
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" fontWeight="bold" ml={1}>
            バックテスト
          </Typography>
        </Box>
        {selectedIds.length >= 2 && (
          <Button
            startIcon={<CompareArrows />}
            size="small"
            onClick={() => setCompareOpen(true)}
          >
            比較
          </Button>
        )}
      </Box>

      {backtests?.length === 0 ? (
        <Alert severity="info">
          バックテストがありません。右下の＋ボタンから作成してください。
        </Alert>
      ) : (
        backtests?.map((bt) => (
          <Card key={bt.id} sx={{ mb: 1 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box display="flex" alignItems="center" gap={1}>
                <Checkbox
                  size="small"
                  checked={selectedIds.includes(bt.id)}
                  onChange={() => toggleSelect(bt.id)}
                />
                <Box
                  flex={1}
                  onClick={() => navigate(`/backtests/${bt.id}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                    <Box>
                      <Typography variant="body1" fontWeight="bold">
                        {bt.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {bt.startDate} ~ {bt.endDate}
                      </Typography>
                    </Box>
                    <Box textAlign="right">
                      <Chip
                        label={bt.status === 'completed' ? '完了' : bt.status === 'running' ? '実行中' : '失敗'}
                        size="small"
                        color={bt.status === 'completed' ? 'success' : bt.status === 'running' ? 'info' : 'error'}
                      />
                      {bt.totalReturnPercent != null && (
                        <Typography
                          variant="body2"
                          fontWeight="bold"
                          color={bt.totalReturnPercent >= 0 ? 'success.main' : 'error.main'}
                          mt={0.5}
                        >
                          {bt.totalReturnPercent >= 0 ? '+' : ''}{bt.totalReturnPercent.toFixed(2)}%
                        </Typography>
                      )}
                    </Box>
                  </Box>
                </Box>
                <IconButton size="small" onClick={() => deleteMutation.mutate(bt.id)}>
                  <Delete fontSize="small" />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        ))
      )}

      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 72, right: 16 }}
        onClick={() => navigate('/backtests/new')}
      >
        <Add />
      </Fab>

      <BacktestCompareDialog
        open={compareOpen}
        onClose={() => setCompareOpen(false)}
        ids={selectedIds}
      />
    </Box>
  );
}
