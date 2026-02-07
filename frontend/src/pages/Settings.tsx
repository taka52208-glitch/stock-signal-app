import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  IconButton,
  Card,
  CardContent,
  TextField,
  Button,
  Slider,
  Alert,
  Snackbar,
  ToggleButton,
  ToggleButtonGroup,
} from '@mui/material';
import { ArrowBack, ChevronRight, Security, AccountBalanceWallet, Science, SmartToy } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { Settings as SettingsType } from '../types';

const DEFAULT_SETTINGS: SettingsType = {
  rsiBuyThreshold: 30,
  rsiSellThreshold: 70,
  smaShortPeriod: 5,
  smaMidPeriod: 25,
  smaLongPeriod: 75,
  investmentBudget: 100000,
};

const BUDGET_PRESETS = [50000, 100000, 300000, 500000, 1000000];

export default function Settings() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [settings, setSettings] = useState<SettingsType>(DEFAULT_SETTINGS);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const { data: savedSettings } = useQuery({
    queryKey: ['settings'],
    queryFn: api.getSettings,
  });

  useEffect(() => {
    if (savedSettings) {
      setSettings(savedSettings);
    }
  }, [savedSettings]);

  const mutation = useMutation({
    mutationFn: api.updateSettings,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setSnackbarOpen(true);
    },
  });

  const handleSave = () => {
    mutation.mutate(settings);
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  return (
    <Box p={2}>
      <Box display="flex" alignItems="center" mb={2}>
        <IconButton onClick={() => navigate('/')}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h6" fontWeight="bold" ml={1}>
          設定
        </Typography>
      </Box>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            RSI 閾値設定
          </Typography>

          <Box mb={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              買いシグナル閾値: {settings.rsiBuyThreshold}以下
            </Typography>
            <Slider
              value={settings.rsiBuyThreshold}
              onChange={(_, value) => setSettings({ ...settings, rsiBuyThreshold: value as number })}
              min={10}
              max={50}
              step={5}
              marks
              valueLabelDisplay="auto"
            />
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              売りシグナル閾値: {settings.rsiSellThreshold}以上
            </Typography>
            <Slider
              value={settings.rsiSellThreshold}
              onChange={(_, value) => setSettings({ ...settings, rsiSellThreshold: value as number })}
              min={50}
              max={90}
              step={5}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            移動平均線 期間設定
          </Typography>

          <Box display="grid" gridTemplateColumns="1fr 1fr 1fr" gap={2}>
            <TextField
              label="短期 (日)"
              type="number"
              size="small"
              value={settings.smaShortPeriod}
              onChange={(e) => setSettings({ ...settings, smaShortPeriod: Number(e.target.value) })}
              inputProps={{ min: 1, max: 50 }}
            />
            <TextField
              label="中期 (日)"
              type="number"
              size="small"
              value={settings.smaMidPeriod}
              onChange={(e) => setSettings({ ...settings, smaMidPeriod: Number(e.target.value) })}
              inputProps={{ min: 10, max: 100 }}
            />
            <TextField
              label="長期 (日)"
              type="number"
              size="small"
              value={settings.smaLongPeriod}
              onChange={(e) => setSettings({ ...settings, smaLongPeriod: Number(e.target.value) })}
              inputProps={{ min: 50, max: 200 }}
            />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            投資予算
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            おすすめ銘柄の購入株数計算に使用されます
          </Typography>
          <ToggleButtonGroup
            value={BUDGET_PRESETS.includes(settings.investmentBudget) ? settings.investmentBudget : null}
            exclusive
            onChange={(_, val) => val != null && setSettings({ ...settings, investmentBudget: val })}
            sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}
          >
            {BUDGET_PRESETS.map((p) => (
              <ToggleButton key={p} value={p} sx={{ flex: '1 1 auto', fontSize: '0.75rem' }}>
                ¥{p.toLocaleString()}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>
          <TextField
            label="カスタム金額"
            type="number"
            fullWidth
            size="small"
            value={settings.investmentBudget}
            onChange={(e) => setSettings({ ...settings, investmentBudget: Number(e.target.value) })}
            inputProps={{ min: 10000 }}
          />
        </CardContent>
      </Card>

      <Box display="flex" gap={2} mb={2}>
        <Button variant="outlined" fullWidth onClick={handleReset}>
          デフォルトに戻す
        </Button>
        <Button
          variant="contained"
          fullWidth
          onClick={handleSave}
          disabled={mutation.isPending}
        >
          保存
        </Button>
      </Box>

      <Card sx={{ mb: 1 }}>
        <CardContent
          sx={{ py: 1.5, '&:last-child': { pb: 1.5 }, cursor: 'pointer' }}
          onClick={() => navigate('/settings/risk')}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <Security color="primary" />
              <Typography variant="body1">リスク管理設定</Typography>
            </Box>
            <ChevronRight color="action" />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 1 }}>
        <CardContent
          sx={{ py: 1.5, '&:last-child': { pb: 1.5 }, cursor: 'pointer' }}
          onClick={() => navigate('/backtests')}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <Science color="primary" />
              <Typography variant="body1">バックテスト</Typography>
            </Box>
            <ChevronRight color="action" />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 1 }}>
        <CardContent
          sx={{ py: 1.5, '&:last-child': { pb: 1.5 }, cursor: 'pointer' }}
          onClick={() => navigate('/settings/brokerage')}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <AccountBalanceWallet color="primary" />
              <Typography variant="body1">証券会社API連携</Typography>
            </Box>
            <ChevronRight color="action" />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 1 }}>
        <CardContent
          sx={{ py: 1.5, '&:last-child': { pb: 1.5 }, cursor: 'pointer' }}
          onClick={() => navigate('/settings/auto-trade')}
        >
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box display="flex" alignItems="center" gap={1}>
              <SmartToy color="primary" />
              <Typography variant="body1">自動売買設定</Typography>
            </Box>
            <ChevronRight color="action" />
          </Box>
        </CardContent>
      </Card>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" onClose={() => setSnackbarOpen(false)}>
          設定を保存しました
        </Alert>
      </Snackbar>
    </Box>
  );
}
