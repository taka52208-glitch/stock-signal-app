import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  List, ListItem, ListItemIcon, ListItemText, Typography, Box, Chip, Alert,
} from '@mui/material';
import { CheckCircle, Warning, Info } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { RiskWarning } from '../types';

interface Props {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  code: string;
  tradeType: string;
  quantity: number;
  price: number;
}

const statusIcon = (status: string) => {
  switch (status) {
    case 'ok': return <CheckCircle color="success" />;
    case 'warning': return <Warning color="warning" />;
    default: return <Info color="info" />;
  }
};

export default function TradeChecklistDialog({ open, onClose, onConfirm, code, tradeType, quantity, price }: Props) {
  const { data: checklist } = useQuery({
    queryKey: ['checklist', code],
    queryFn: () => api.getChecklist(code),
    enabled: open && !!code,
  });

  const { data: evaluation } = useQuery({
    queryKey: ['evaluateTrade', code, tradeType, quantity, price],
    queryFn: () => api.evaluateTrade({ code, tradeType, quantity, price }),
    enabled: open && !!code && quantity > 0 && price > 0,
  });

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs">
      <DialogTitle>取引前チェックリスト</DialogTitle>
      <DialogContent>
        {checklist && (
          <>
            <Typography variant="subtitle2" color="text.secondary" mb={1}>
              {checklist.name}（{checklist.code}）
            </Typography>
            <List dense>
              {checklist.items.map((item, i) => (
                <ListItem key={i} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    {statusIcon(item.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.label}
                    secondary={item.detail}
                    primaryTypographyProps={{ variant: 'body2' }}
                    secondaryTypographyProps={{ variant: 'caption' }}
                  />
                </ListItem>
              ))}
            </List>
          </>
        )}

        {evaluation && (
          <Box mt={2}>
            <Typography variant="subtitle2" fontWeight="bold" mb={1}>
              リスク評価
            </Typography>
            <Box display="flex" gap={1} mb={1}>
              <Chip
                label={evaluation.passed ? '問題なし' : '注意あり'}
                color={evaluation.passed ? 'success' : 'warning'}
                size="small"
              />
              <Chip
                label={`取引額: ¥${evaluation.tradeAmount.toLocaleString()}`}
                size="small"
                variant="outlined"
              />
            </Box>
            {evaluation.warnings.map((w: RiskWarning, i: number) => (
              <Alert key={i} severity={w.level === 'error' ? 'error' : 'warning'} sx={{ mb: 0.5 }}>
                {w.message}
              </Alert>
            ))}
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>キャンセル</Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color={evaluation?.passed === false ? 'warning' : 'primary'}
        >
          {evaluation?.passed === false ? 'リスクを承知で実行' : '取引を実行'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
