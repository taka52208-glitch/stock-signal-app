import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, IconButton, Card, CardContent, Switch, Slider,
  Button, Alert, Snackbar, Chip, ToggleButton, ToggleButtonGroup,
  List, ListItem, ListItemText, ListItemSecondaryAction, Divider,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { AutoTradeConfig, AutoTradeStockSetting, AutoTradeLog } from '../types';

const DEFAULT_CONFIG: AutoTradeConfig = {
  enabled: false,
  minSignalStrength: 2,
  maxTradesPerDay: 3,
  orderType: 'market',
  dryRun: true,
};

const STATUS_LABELS: Record<string, { label: string; color: 'success' | 'error' | 'warning' | 'default' }> = {
  success: { label: '成功', color: 'success' },
  failed: { label: '失敗', color: 'error' },
  skipped: { label: 'スキップ', color: 'default' },
  risk_blocked: { label: 'リスク拒否', color: 'warning' },
};

export default function AutoTradeSettings() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<AutoTradeConfig>(DEFAULT_CONFIG);
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success',
  });

  const { data: savedConfig } = useQuery({
    queryKey: ['autoTradeConfig'],
    queryFn: api.getAutoTradeConfig,
  });

  const { data: stocks = [] } = useQuery({
    queryKey: ['autoTradeStocks'],
    queryFn: api.getAutoTradeStocks,
  });

  const { data: logs = [] } = useQuery({
    queryKey: ['autoTradeLog'],
    queryFn: () => api.getAutoTradeLog(30),
  });

  const { data: virtualPortfolio } = useQuery({
    queryKey: ['virtualPortfolio'],
    queryFn: api.getVirtualPortfolio,
  });

  useEffect(() => {
    if (savedConfig) setConfig(savedConfig);
  }, [savedConfig]);

  const configMutation = useMutation({
    mutationFn: api.updateAutoTradeConfig,
    onSuccess: (data) => {
      setConfig(data);
      queryClient.invalidateQueries({ queryKey: ['autoTradeConfig'] });
      setSnackbar({ open: true, message: '設定を保存しました', severity: 'success' });
    },
    onError: () => setSnackbar({ open: true, message: '保存に失敗しました', severity: 'error' }),
  });

  const toggleMutation = useMutation({
    mutationFn: api.toggleAutoTrade,
    onMutate: async (enabled) => {
      await queryClient.cancelQueries({ queryKey: ['autoTradeConfig'] });
      const previous = queryClient.getQueryData<AutoTradeConfig>(['autoTradeConfig']);
      queryClient.setQueryData<AutoTradeConfig>(['autoTradeConfig'], (old) =>
        old ? { ...old, enabled } : undefined,
      );
      setConfig(prev => ({ ...prev, enabled }));
      return { previous };
    },
    onError: (_err, _enabled, context) => {
      if (context?.previous) {
        queryClient.setQueryData(['autoTradeConfig'], context.previous);
        setConfig(context.previous);
      }
      setSnackbar({ open: true, message: '切り替えに失敗しました', severity: 'error' });
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['autoTradeConfig'] });
    },
  });

  const stockMutation = useMutation({
    mutationFn: ({ code, enabled }: { code: string; enabled: boolean }) =>
      api.updateAutoTradeStock(code, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['autoTradeStocks'] }),
  });

  const handleSave = () => {
    const { enabled, ...rest } = config;
    configMutation.mutate(rest);
  };

  const handleToggle = (enabled: boolean) => {
    toggleMutation.mutate(enabled);
  };

  return (
    <Box p={2}>
      <Box display="flex" alignItems="center" mb={2}>
        <IconButton onClick={() => navigate('/settings')}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h6" fontWeight="bold" ml={1}>
          自動売買設定
        </Typography>
      </Box>

      <Alert severity="warning" sx={{ mb: 2 }}>
        自動売買は実際のお金を使って取引を行います。
        必ずドライランモードで動作を確認してから有効化してください。
      </Alert>

      {/* グローバルON/OFF */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="subtitle1" fontWeight="bold">
                自動売買
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {config.enabled ? '有効' : '無効'}
              </Typography>
            </Box>
            <Switch
              checked={config.enabled}
              onChange={(e) => handleToggle(e.target.checked)}
              color="primary"
            />
          </Box>
        </CardContent>
      </Card>

      {/* ドライランモード */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
            <Box>
              <Typography variant="subtitle1" fontWeight="bold">
                ドライランモード
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {config.dryRun ? 'ON (ログのみ)' : 'OFF (実注文)'}
              </Typography>
            </Box>
            <Switch
              checked={config.dryRun}
              onChange={(e) => setConfig(prev => ({ ...prev, dryRun: e.target.checked }))}
              color="warning"
            />
          </Box>
          {!config.dryRun && (
            <Alert severity="error" variant="outlined" sx={{ mt: 1 }}>
              ドライランがOFFです。実際の注文が証券会社に送信されます。
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* 仮想収支（ドライラン） */}
      {virtualPortfolio && virtualPortfolio.tradeCount > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent sx={{ pb: 1 }}>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={1}>
              <Typography variant="subtitle1" fontWeight="bold">
                仮想収支 (DRY-RUN)
              </Typography>
              <Chip
                label={`${virtualPortfolio.totalProfitLoss >= 0 ? '+' : ''}${virtualPortfolio.totalProfitLoss.toLocaleString()}円`}
                color={virtualPortfolio.totalProfitLoss >= 0 ? 'success' : 'error'}
                size="small"
              />
            </Box>
            {/* 実現 / 含み損益の内訳 */}
            <Box display="flex" justifyContent="space-between" mb={0.5}>
              <Typography variant="body2" color="text.secondary">
                実現損益:
              </Typography>
              <Typography
                variant="body2"
                fontWeight="bold"
                color={virtualPortfolio.realizedProfitLoss >= 0 ? 'success.main' : 'error.main'}
              >
                {virtualPortfolio.realizedProfitLoss >= 0 ? '+' : ''}
                {virtualPortfolio.realizedProfitLoss.toLocaleString()}円
              </Typography>
            </Box>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2" color="text.secondary">
                含み損益:
              </Typography>
              <Typography
                variant="body2"
                fontWeight="bold"
                color={virtualPortfolio.unrealizedProfitLoss >= 0 ? 'success.main' : 'error.main'}
              >
                {virtualPortfolio.unrealizedProfitLoss >= 0 ? '+' : ''}
                {virtualPortfolio.unrealizedProfitLoss.toLocaleString()}円
              </Typography>
            </Box>
            <Divider sx={{ mb: 1 }} />
            <Box display="flex" justifyContent="space-between" mb={0.5}>
              <Typography variant="body2" color="text.secondary">
                投入: {virtualPortfolio.totalCost.toLocaleString()}円
              </Typography>
              <Typography variant="body2" color="text.secondary">
                評価: {virtualPortfolio.totalValue.toLocaleString()}円
              </Typography>
            </Box>
            <Box display="flex" justifyContent="space-between">
              <Typography variant="body2" color="text.secondary">
                取引回数: {virtualPortfolio.tradeCount}回
              </Typography>
              <Typography
                variant="body2"
                fontWeight="bold"
                color={virtualPortfolio.totalProfitLoss >= 0 ? 'success.main' : 'error.main'}
              >
                合計: {virtualPortfolio.totalProfitLossPercent >= 0 ? '+' : ''}
                {virtualPortfolio.totalProfitLossPercent.toFixed(2)}%
              </Typography>
            </Box>
          </CardContent>
          {virtualPortfolio.holdings.length > 0 && (
            <TableContainer sx={{ mx: 2, mb: 2, width: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontSize: '0.75rem', px: 1 }}>銘柄</TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.75rem', px: 1 }}>数量</TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.75rem', px: 1 }}>取得</TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.75rem', px: 1 }}>現在</TableCell>
                    <TableCell align="right" sx={{ fontSize: '0.75rem', px: 1 }}>損益</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {virtualPortfolio.holdings.map((h) => (
                    <TableRow key={h.code}>
                      <TableCell sx={{ fontSize: '0.75rem', px: 1 }}>
                        {h.code} {h.name.length > 6 ? h.name.slice(0, 6) + '..' : h.name}
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.75rem', px: 1 }}>
                        {h.quantity}
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.75rem', px: 1 }}>
                        {h.averagePrice.toLocaleString()}
                      </TableCell>
                      <TableCell align="right" sx={{ fontSize: '0.75rem', px: 1 }}>
                        {h.currentPrice.toLocaleString()}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{
                          fontSize: '0.75rem', px: 1, fontWeight: 'bold',
                          color: h.profitLoss >= 0 ? 'success.main' : 'error.main',
                        }}
                      >
                        {h.profitLoss >= 0 ? '+' : ''}{h.profitLoss.toLocaleString()}
                        <Typography component="span" sx={{ fontSize: '0.6rem', ml: 0.5 }}>
                          ({h.profitLossPercent >= 0 ? '+' : ''}{h.profitLossPercent.toFixed(1)}%)
                        </Typography>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Card>
      )}

      {/* 取引設定 */}
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            取引条件
          </Typography>

          <Box mb={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              最低シグナル強度: {config.minSignalStrength} / 3
            </Typography>
            <Slider
              value={config.minSignalStrength}
              onChange={(_, v) => setConfig(prev => ({ ...prev, minSignalStrength: v as number }))}
              min={1}
              max={3}
              step={1}
              marks={[
                { value: 1, label: '1 (弱)' },
                { value: 2, label: '2 (中)' },
                { value: 3, label: '3 (強)' },
              ]}
              valueLabelDisplay="off"
            />
          </Box>

          <Box mb={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              1日の最大取引数: {config.maxTradesPerDay}
            </Typography>
            <Slider
              value={config.maxTradesPerDay}
              onChange={(_, v) => setConfig(prev => ({ ...prev, maxTradesPerDay: v as number }))}
              min={1}
              max={10}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              注文タイプ
            </Typography>
            <ToggleButtonGroup
              value={config.orderType}
              exclusive
              onChange={(_, v) => v && setConfig(prev => ({ ...prev, orderType: v }))}
              fullWidth
            >
              <ToggleButton value="market">成行</ToggleButton>
              <ToggleButton value="limit">指値</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </CardContent>
      </Card>

      <Button
        variant="contained"
        fullWidth
        onClick={handleSave}
        disabled={configMutation.isPending}
        sx={{ mb: 2 }}
      >
        設定を保存
      </Button>

      {/* 銘柄別設定 */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ pb: 0 }}>
          <Typography variant="subtitle1" fontWeight="bold" mb={1}>
            対象銘柄
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={1}>
            自動売買の対象にする銘柄を選択
          </Typography>
        </CardContent>
        {stocks.length === 0 ? (
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              監視銘柄が登録されていません
            </Typography>
          </CardContent>
        ) : (
          <List dense>
            {stocks.map((stock: AutoTradeStockSetting, idx: number) => (
              <Box key={stock.code}>
                {idx > 0 && <Divider />}
                <ListItem>
                  <ListItemText
                    primary={`${stock.code} ${stock.name}`}
                  />
                  <ListItemSecondaryAction>
                    <Switch
                      edge="end"
                      checked={stock.enabled}
                      onChange={(e) => stockMutation.mutate({ code: stock.code, enabled: e.target.checked })}
                    />
                  </ListItemSecondaryAction>
                </ListItem>
              </Box>
            ))}
          </List>
        )}
      </Card>

      {/* 実行ログ */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ pb: 1 }}>
          <Typography variant="subtitle1" fontWeight="bold" mb={1}>
            実行ログ (直近30件)
          </Typography>
        </CardContent>
        {logs.length === 0 ? (
          <CardContent>
            <Typography variant="body2" color="text.secondary">
              ログはありません
            </Typography>
          </CardContent>
        ) : (
          <TableContainer component={Paper} variant="outlined" sx={{ mx: 2, mb: 2, width: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>日時</TableCell>
                  <TableCell>銘柄</TableCell>
                  <TableCell>シグナル</TableCell>
                  <TableCell>ステータス</TableCell>
                  <TableCell>理由</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {logs.map((log: AutoTradeLog) => {
                  const status = STATUS_LABELS[log.resultStatus] || { label: log.resultStatus, color: 'default' as const };
                  const signalLabel = log.signalType === 'buy' ? '買' : log.signalType === 'sell' ? '売' : '様子見';
                  const signalColor = log.signalType === 'buy' ? 'success'
                    : log.signalType === 'sell' ? 'error' : 'default';
                  return (
                    <TableRow key={log.id}>
                      <TableCell sx={{ fontSize: '0.75rem', whiteSpace: 'nowrap' }}>
                        {log.createdAt ? new Date(log.createdAt).toLocaleString('ja-JP', {
                          month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit',
                        }) : '-'}
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.75rem' }}>{log.code}</TableCell>
                      <TableCell>
                        <Chip
                          label={signalLabel}
                          size="small"
                          color={signalColor as 'success' | 'error' | 'default'}
                          variant="outlined"
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                        {log.dryRun && (
                          <Chip label="DRY" size="small" sx={{ fontSize: '0.6rem', height: 16, ml: 0.5 }} />
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={status.label}
                          size="small"
                          color={status.color}
                          sx={{ fontSize: '0.7rem', height: 20 }}
                        />
                      </TableCell>
                      <TableCell sx={{ fontSize: '0.7rem', maxWidth: 200 }}>
                        {log.resultMessage || '-'}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
