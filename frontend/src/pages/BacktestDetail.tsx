import { useParams, useNavigate } from 'react-router-dom';
import {
  Box, Typography, IconButton, Card, CardContent, Chip,
  CircularProgress, Alert, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import PerformanceMetricsCard from '../components/PerformanceMetricsCard';
import EquityCurveChart from '../components/EquityCurveChart';

export default function BacktestDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const backtestId = parseInt(id!);

  const { data: backtest, isLoading } = useQuery({
    queryKey: ['backtest', backtestId],
    queryFn: () => api.getBacktest(backtestId),
    enabled: !!id,
  });

  const { data: trades } = useQuery({
    queryKey: ['backtestTrades', backtestId],
    queryFn: () => api.getBacktestTrades(backtestId),
    enabled: !!id,
  });

  const { data: snapshots } = useQuery({
    queryKey: ['backtestSnapshots', backtestId],
    queryFn: () => api.getBacktestSnapshots(backtestId),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (!backtest) {
    return (
      <Box p={2}>
        <Alert severity="error">バックテストが見つかりません</Alert>
      </Box>
    );
  }

  return (
    <Box p={2}>
      <Box display="flex" alignItems="center" mb={2}>
        <IconButton onClick={() => navigate(-1)}>
          <ArrowBack />
        </IconButton>
        <Box ml={1}>
          <Typography variant="h6" fontWeight="bold">
            {backtest.name}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {backtest.startDate} ~ {backtest.endDate}
          </Typography>
        </Box>
        <Box ml="auto">
          <Chip
            label={backtest.status === 'completed' ? '完了' : backtest.status === 'running' ? '実行中' : '失敗'}
            color={backtest.status === 'completed' ? 'success' : backtest.status === 'running' ? 'info' : 'error'}
            size="small"
          />
        </Box>
      </Box>

      {backtest.status === 'completed' && backtest.resultSummary && (
        <>
          <PerformanceMetricsCard
            summary={backtest.resultSummary}
            initialCapital={backtest.initialCapital}
          />

          {snapshots && snapshots.length > 0 && (
            <EquityCurveChart
              snapshots={snapshots}
              initialCapital={backtest.initialCapital}
            />
          )}
        </>
      )}

      {backtest.status === 'failed' && backtest.resultSummary && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {(backtest.resultSummary as Record<string, unknown>).error as string || 'バックテストが失敗しました'}
        </Alert>
      )}

      {trades && trades.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" fontWeight="bold" mb={2}>
              取引一覧（{trades.length}件）
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>日付</TableCell>
                    <TableCell>銘柄</TableCell>
                    <TableCell>売買</TableCell>
                    <TableCell align="right">数量</TableCell>
                    <TableCell align="right">価格</TableCell>
                    <TableCell align="right">損益</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {trades.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell>
                        <Typography variant="caption">{t.tradeDate}</Typography>
                      </TableCell>
                      <TableCell>{t.code}</TableCell>
                      <TableCell>
                        <Chip
                          label={t.tradeType === 'buy' ? '買' : '売'}
                          size="small"
                          color={t.tradeType === 'buy' ? 'success' : 'error'}
                        />
                      </TableCell>
                      <TableCell align="right">{t.quantity}</TableCell>
                      <TableCell align="right">¥{t.price.toLocaleString()}</TableCell>
                      <TableCell align="right">
                        {t.pnl != null ? (
                          <Typography
                            variant="body2"
                            color={t.pnl >= 0 ? 'success.main' : 'error.main'}
                          >
                            {t.pnl >= 0 ? '+' : ''}¥{t.pnl.toLocaleString()}
                          </Typography>
                        ) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Box>
  );
}
