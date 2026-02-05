import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Add, Delete, Refresh, TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { Stock, SignalType } from '../types';

const getSignalColor = (signal: SignalType) => {
  switch (signal) {
    case 'buy':
      return 'success';
    case 'sell':
      return 'error';
    default:
      return 'default';
  }
};

const getSignalIcon = (signal: SignalType) => {
  switch (signal) {
    case 'buy':
      return <TrendingUp />;
    case 'sell':
      return <TrendingDown />;
    default:
      return <TrendingFlat />;
  }
};

const getSignalLabel = (signal: SignalType) => {
  switch (signal) {
    case 'buy':
      return '買い';
    case 'sell':
      return '売り';
    default:
      return '様子見';
  }
};

export default function StockList() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [openDialog, setOpenDialog] = useState(false);
  const [newStockCode, setNewStockCode] = useState('');

  const { data: stocks, isLoading, error } = useQuery({
    queryKey: ['stocks'],
    queryFn: api.getStocks,
  });

  const addMutation = useMutation({
    mutationFn: api.addStock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] });
      setOpenDialog(false);
      setNewStockCode('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteStock,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: api.triggerUpdate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] });
    },
  });

  const handleAddStock = () => {
    if (newStockCode.match(/^\d{4}$/)) {
      addMutation.mutate({ code: newStockCode });
    }
  };

  const handleDeleteStock = (e: React.MouseEvent, code: string) => {
    e.stopPropagation();
    if (confirm('この銘柄を削除しますか？')) {
      deleteMutation.mutate(code);
    }
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
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" fontWeight="bold">
          監視銘柄
        </Typography>
        <IconButton onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending}>
          <Refresh />
        </IconButton>
      </Box>

      {stocks?.length === 0 ? (
        <Alert severity="info">監視銘柄がありません。右下の＋ボタンから追加してください。</Alert>
      ) : (
        stocks?.map((stock: Stock) => (
          <Card
            key={stock.code}
            sx={{ mb: 1, cursor: 'pointer' }}
            onClick={() => navigate(`/stock/${stock.code}`)}
          >
            <CardContent sx={{ display: 'flex', alignItems: 'center', py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box flex={1}>
                <Typography variant="subtitle2" color="text.secondary">
                  {stock.code}
                </Typography>
                <Typography variant="body1" fontWeight="bold">
                  {stock.name}
                </Typography>
                <Typography
                  variant="body2"
                  color={stock.changePercent >= 0 ? 'success.main' : 'error.main'}
                >
                  ¥{stock.currentPrice.toLocaleString()}{' '}
                  ({stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)
                </Typography>
              </Box>
              <Box display="flex" alignItems="center" gap={1}>
                <Chip
                  icon={getSignalIcon(stock.signal)}
                  label={getSignalLabel(stock.signal)}
                  color={getSignalColor(stock.signal)}
                  size="small"
                />
                <IconButton
                  size="small"
                  onClick={(e) => handleDeleteStock(e, stock.code)}
                  disabled={deleteMutation.isPending}
                >
                  <Delete fontSize="small" />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        ))
      )}

      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => setOpenDialog(true)}
      >
        <Add />
      </Fab>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>銘柄を追加</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="銘柄コード（4桁）"
            fullWidth
            value={newStockCode}
            onChange={(e) => setNewStockCode(e.target.value)}
            placeholder="例: 7203"
            inputProps={{ maxLength: 4, pattern: '[0-9]*' }}
            error={newStockCode.length > 0 && !newStockCode.match(/^\d{4}$/)}
            helperText={newStockCode.length > 0 && !newStockCode.match(/^\d{4}$/) ? '4桁の数字を入力してください' : ''}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>キャンセル</Button>
          <Button
            onClick={handleAddStock}
            variant="contained"
            disabled={!newStockCode.match(/^\d{4}$/) || addMutation.isPending}
          >
            追加
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
