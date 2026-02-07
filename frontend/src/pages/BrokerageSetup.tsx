import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, IconButton, Card, CardContent, TextField, Button,
  Alert, Snackbar, CircularProgress,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import BrokerageStatusBadge from '../components/BrokerageStatusBadge';
import type { BrokerageConfig } from '../types';

const DEFAULT_CONFIG: BrokerageConfig = {
  host: 'localhost',
  port: 18080,
  apiPassword: '',
};

export default function BrokerageSetup() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [config, setConfig] = useState<BrokerageConfig>(DEFAULT_CONFIG);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [connected, setConnected] = useState(false);
  const [connectMessage, setConnectMessage] = useState('');

  const { data: savedConfig, isLoading } = useQuery({
    queryKey: ['brokerageConfig'],
    queryFn: api.getBrokerageConfig,
  });

  useEffect(() => {
    if (savedConfig) setConfig(savedConfig);
  }, [savedConfig]);

  const saveMutation = useMutation({
    mutationFn: api.updateBrokerageConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['brokerageConfig'] });
      setSnackbarOpen(true);
    },
  });

  const connectMutation = useMutation({
    mutationFn: api.connectBrokerage,
    onSuccess: (data) => {
      setConnected(data.connected);
      setConnectMessage(data.message);
    },
  });

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
            証券会社API連携
          </Typography>
        </Box>
        <BrokerageStatusBadge connected={connected} />
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        kabu STATION APIを使用します。kabu STATIONデスクトップアプリを起動した状態で接続してください。
      </Alert>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            接続設定
          </Typography>
          <TextField
            label="ホスト"
            fullWidth
            margin="dense"
            value={config.host}
            onChange={(e) => setConfig({ ...config, host: e.target.value })}
          />
          <TextField
            label="ポート"
            type="number"
            fullWidth
            margin="dense"
            value={config.port}
            onChange={(e) => setConfig({ ...config, port: parseInt(e.target.value) })}
          />
          <TextField
            label="APIパスワード"
            type="password"
            fullWidth
            margin="dense"
            value={config.apiPassword}
            onChange={(e) => setConfig({ ...config, apiPassword: e.target.value })}
          />
        </CardContent>
      </Card>

      <Box display="flex" gap={2} mb={2}>
        <Button
          variant="outlined"
          fullWidth
          onClick={() => saveMutation.mutate(config)}
          disabled={saveMutation.isPending}
        >
          設定を保存
        </Button>
        <Button
          variant="contained"
          fullWidth
          onClick={() => connectMutation.mutate()}
          disabled={connectMutation.isPending}
        >
          {connectMutation.isPending ? '接続中...' : '接続テスト'}
        </Button>
      </Box>

      {connectMessage && (
        <Alert severity={connected ? 'success' : 'error'} sx={{ mb: 2 }}>
          {connectMessage}
        </Alert>
      )}

      {connected && (
        <Card>
          <CardContent>
            <Typography variant="subtitle1" fontWeight="bold" mb={1}>
              利用可能な機能
            </Typography>
            <Button fullWidth variant="text" onClick={() => navigate('/orders')} sx={{ justifyContent: 'flex-start' }}>
              注文管理
            </Button>
          </CardContent>
        </Card>
      )}

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
