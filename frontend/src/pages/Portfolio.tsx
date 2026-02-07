import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  CircularProgress,
  Alert,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import { Add } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { TransactionType } from '../types';
import TradeChecklistDialog from '../components/TradeChecklistDialog';

export default function Portfolio() {
  const queryClient = useQueryClient();
  const [openDialog, setOpenDialog] = useState(false);
  const [checklistOpen, setChecklistOpen] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    transactionType: 'buy' as TransactionType,
    quantity: '',
    price: '',
    memo: '',
  });

  const { data: portfolio, isLoading, error } = useQuery({
    queryKey: ['portfolio'],
    queryFn: api.getPortfolio,
  });

  const addMutation = useMutation({
    mutationFn: api.addTransaction,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['transactions'] });
      setOpenDialog(false);
      setFormData({ code: '', transactionType: 'buy', quantity: '', price: '', memo: '' });
    },
  });

  const handleSubmit = () => {
    if (!formData.code.match(/^\d{4}$/) || !formData.quantity || !formData.price) return;
    setOpenDialog(false);
    setChecklistOpen(true);
  };

  const handleConfirmTrade = () => {
    setChecklistOpen(false);
    addMutation.mutate({
      code: formData.code,
      transactionType: formData.transactionType,
      quantity: parseInt(formData.quantity),
      price: parseFloat(formData.price),
      memo: formData.memo || undefined,
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
        ポートフォリオ
      </Typography>

      {/* サマリーカード */}
      <Card sx={{ mb: 2, bgcolor: 'primary.main', color: 'white' }}>
        <CardContent>
          <Typography variant="body2" sx={{ opacity: 0.8 }}>
            評価額合計
          </Typography>
          <Typography variant="h4" fontWeight="bold">
            ¥{portfolio?.totalValue.toLocaleString() || 0}
          </Typography>
          <Box display="flex" gap={2} mt={1}>
            <Box>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                取得額
              </Typography>
              <Typography variant="body2">
                ¥{portfolio?.totalCost.toLocaleString() || 0}
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" sx={{ opacity: 0.8 }}>
                損益
              </Typography>
              <Typography
                variant="body2"
                sx={{ color: (portfolio?.totalProfitLoss || 0) >= 0 ? '#90EE90' : '#FFB6C1' }}
              >
                {(portfolio?.totalProfitLoss || 0) >= 0 ? '+' : ''}
                ¥{portfolio?.totalProfitLoss.toLocaleString() || 0}
                ({(portfolio?.totalProfitLossPercent || 0) >= 0 ? '+' : ''}
                {portfolio?.totalProfitLossPercent.toFixed(2) || 0}%)
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* 保有株リスト */}
      {portfolio?.holdings.length === 0 ? (
        <Alert severity="info">
          保有株がありません。右下の＋ボタンから取引を記録してください。
        </Alert>
      ) : (
        portfolio?.holdings.map((holding) => (
          <Card key={holding.code} sx={{ mb: 1 }}>
            <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
              <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    {holding.code}
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {holding.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {holding.quantity}株 × ¥{holding.averagePrice.toLocaleString()}
                  </Typography>
                </Box>
                <Box textAlign="right">
                  <Typography variant="body1" fontWeight="bold">
                    ¥{holding.currentValue.toLocaleString()}
                  </Typography>
                  <Typography
                    variant="body2"
                    color={holding.profitLoss >= 0 ? 'success.main' : 'error.main'}
                  >
                    {holding.profitLoss >= 0 ? '+' : ''}¥{holding.profitLoss.toLocaleString()}
                    ({holding.profitLossPercent >= 0 ? '+' : ''}{holding.profitLossPercent.toFixed(2)}%)
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        ))
      )}

      {/* 取引追加ボタン */}
      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 72, right: 16 }}
        onClick={() => setOpenDialog(true)}
      >
        <Add />
      </Fab>

      {/* 取引追加ダイアログ */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} fullWidth maxWidth="xs">
        <DialogTitle>取引を記録</DialogTitle>
        <DialogContent>
          <ToggleButtonGroup
            value={formData.transactionType}
            exclusive
            onChange={(_, value) => value && setFormData({ ...formData, transactionType: value })}
            fullWidth
            sx={{ mb: 2, mt: 1 }}
          >
            <ToggleButton value="buy" color="success">
              買い
            </ToggleButton>
            <ToggleButton value="sell" color="error">
              売り
            </ToggleButton>
          </ToggleButtonGroup>

          <TextField
            label="銘柄コード（4桁）"
            fullWidth
            margin="dense"
            value={formData.code}
            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
            inputProps={{ maxLength: 4 }}
            error={formData.code.length > 0 && !formData.code.match(/^\d{4}$/)}
          />
          <TextField
            label="株数"
            type="number"
            fullWidth
            margin="dense"
            value={formData.quantity}
            onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
            inputProps={{ min: 1 }}
          />
          <TextField
            label="単価（円）"
            type="number"
            fullWidth
            margin="dense"
            value={formData.price}
            onChange={(e) => setFormData({ ...formData, price: e.target.value })}
            inputProps={{ min: 0, step: 0.1 }}
          />
          <TextField
            label="メモ（任意）"
            fullWidth
            margin="dense"
            value={formData.memo}
            onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>キャンセル</Button>
          <Button
            onClick={handleSubmit}
            variant="contained"
            disabled={
              !formData.code.match(/^\d{4}$/) ||
              !formData.quantity ||
              !formData.price ||
              addMutation.isPending
            }
          >
            記録
          </Button>
        </DialogActions>
      </Dialog>

      <TradeChecklistDialog
        open={checklistOpen}
        onClose={() => { setChecklistOpen(false); setOpenDialog(true); }}
        onConfirm={handleConfirmTrade}
        code={formData.code}
        tradeType={formData.transactionType}
        quantity={parseInt(formData.quantity) || 0}
        price={parseFloat(formData.price) || 0}
      />
    </Box>
  );
}
