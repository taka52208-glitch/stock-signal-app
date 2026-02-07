import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  TextField, ToggleButton, ToggleButtonGroup,
} from '@mui/material';
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

interface Props {
  open: boolean;
  onClose: () => void;
  defaultCode?: string;
}

export default function OrderDialog({ open, onClose, defaultCode }: Props) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    code: defaultCode || '',
    orderType: 'market' as 'market' | 'limit' | 'stop',
    side: 'buy' as 'buy' | 'sell',
    quantity: '',
    price: '',
  });

  const mutation = useMutation({
    mutationFn: api.createOrder,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      onClose();
      setFormData({ code: defaultCode || '', orderType: 'market', side: 'buy', quantity: '', price: '' });
    },
  });

  const handleSubmit = () => {
    if (!formData.code.match(/^\d{4}$/) || !formData.quantity) return;
    mutation.mutate({
      code: formData.code,
      orderType: formData.orderType,
      side: formData.side,
      quantity: parseInt(formData.quantity),
      price: formData.orderType !== 'market' ? parseFloat(formData.price) : undefined,
    });
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>注文</DialogTitle>
      <DialogContent>
        <ToggleButtonGroup
          value={formData.side}
          exclusive
          onChange={(_, v) => v && setFormData({ ...formData, side: v })}
          fullWidth
          sx={{ mb: 2, mt: 1 }}
        >
          <ToggleButton value="buy" color="success">買い</ToggleButton>
          <ToggleButton value="sell" color="error">売り</ToggleButton>
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

        <ToggleButtonGroup
          value={formData.orderType}
          exclusive
          onChange={(_, v) => v && setFormData({ ...formData, orderType: v })}
          fullWidth
          sx={{ my: 2 }}
          size="small"
        >
          <ToggleButton value="market">成行</ToggleButton>
          <ToggleButton value="limit">指値</ToggleButton>
          <ToggleButton value="stop">逆指値</ToggleButton>
        </ToggleButtonGroup>

        <TextField
          label="株数"
          type="number"
          fullWidth
          margin="dense"
          value={formData.quantity}
          onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
          inputProps={{ min: 1 }}
        />

        {formData.orderType !== 'market' && (
          <TextField
            label="価格（円）"
            type="number"
            fullWidth
            margin="dense"
            value={formData.price}
            onChange={(e) => setFormData({ ...formData, price: e.target.value })}
            inputProps={{ min: 0 }}
          />
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>キャンセル</Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          color={formData.side === 'buy' ? 'success' : 'error'}
          disabled={
            !formData.code.match(/^\d{4}$/) || !formData.quantity ||
            (formData.orderType !== 'market' && !formData.price) ||
            mutation.isPending
          }
        >
          注文送信
        </Button>
      </DialogActions>
    </Dialog>
  );
}
