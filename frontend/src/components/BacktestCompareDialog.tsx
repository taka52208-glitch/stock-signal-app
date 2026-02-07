import {
  Dialog, DialogTitle, DialogContent, DialogActions, Button,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Typography, CircularProgress, Box,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import type { BacktestDetail } from '../types';

interface Props {
  open: boolean;
  onClose: () => void;
  ids: number[];
}

export default function BacktestCompareDialog({ open, onClose, ids }: Props) {
  const { data, isLoading } = useQuery({
    queryKey: ['backtestCompare', ids],
    queryFn: () => api.compareBacktests(ids),
    enabled: open && ids.length >= 2,
  });

  const metrics = ['totalReturnPercent', 'maxDrawdown', 'winRate', 'profitFactor', 'sharpeRatio', 'totalTrades'];
  const labels: Record<string, string> = {
    totalReturnPercent: 'リターン(%)',
    maxDrawdown: '最大DD(%)',
    winRate: '勝率(%)',
    profitFactor: 'PF',
    sharpeRatio: 'シャープ',
    totalTrades: '取引数',
  };

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>バックテスト比較</DialogTitle>
      <DialogContent>
        {isLoading ? (
          <Box display="flex" justifyContent="center" py={4}><CircularProgress /></Box>
        ) : data?.backtests ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>指標</TableCell>
                  {data.backtests.map((bt: BacktestDetail) => (
                    <TableCell key={bt.id} align="right">
                      <Typography variant="caption" fontWeight="bold">{bt.name}</Typography>
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {metrics.map((m) => (
                  <TableRow key={m}>
                    <TableCell>{labels[m]}</TableCell>
                    {data.backtests.map((bt: BacktestDetail) => (
                      <TableCell key={bt.id} align="right">
                        {bt.resultSummary ? (bt.resultSummary[m] as number)?.toFixed?.(2) ?? bt.resultSummary[m] : '-'}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : null}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
}
