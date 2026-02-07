import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  IconButton,
  Card,
  CardContent,
  Chip,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Alert,
} from '@mui/material';
import { ArrowBack, TrendingUp, TrendingDown, TrendingFlat } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { api } from '../api/client';
import type { SignalType } from '../types';
import SignalStrengthDisplay from '../components/SignalStrengthDisplay';

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

export default function StockDetail() {
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const [period, setPeriod] = useState('3m');

  const { data: stock, isLoading: stockLoading, error: stockError } = useQuery({
    queryKey: ['stock', code],
    queryFn: () => api.getStockDetail(code!),
    enabled: !!code,
  });

  const { data: chartData, isLoading: chartLoading } = useQuery({
    queryKey: ['chart', code, period],
    queryFn: () => api.getChartData(code!, period),
    enabled: !!code,
  });

  if (stockLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (stockError || !stock) {
    return (
      <Box p={2}>
        <Alert severity="error">銘柄データの取得に失敗しました</Alert>
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
          <Typography variant="subtitle2" color="text.secondary">
            {stock.code}
          </Typography>
          <Typography variant="h6" fontWeight="bold">
            {stock.name}
          </Typography>
        </Box>
      </Box>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h4" fontWeight="bold">
                ¥{stock.currentPrice.toLocaleString()}
              </Typography>
              <Typography
                variant="body1"
                color={stock.changePercent >= 0 ? 'success.main' : 'error.main'}
              >
                {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                （前日比 ¥{(stock.currentPrice - stock.previousClose).toLocaleString()}）
              </Typography>
            </Box>
            <Box textAlign="right">
              <Chip
                icon={getSignalIcon(stock.signal)}
                label={getSignalLabel(stock.signal)}
                color={getSignalColor(stock.signal)}
              />
              {stock.signalStrength > 0 && (
                <Box mt={0.5}>
                  <SignalStrengthDisplay strength={stock.signalStrength} />
                </Box>
              )}
            </Box>
          </Box>
        </CardContent>
      </Card>

      {(stock.targetPrice || stock.stopLossPrice) && (
        <Card sx={{ mb: 2, border: '1px solid', borderColor: stock.signal === 'buy' ? 'success.light' : stock.signal === 'sell' ? 'error.light' : 'grey.300' }}>
          <CardContent>
            <Typography variant="subtitle1" fontWeight="bold" mb={2}>
              売買目安
            </Typography>
            <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
              {stock.targetPrice != null && (
                <Box>
                  <Typography variant="caption" color="text.secondary">目標価格</Typography>
                  <Typography variant="h6" fontWeight="bold" color="success.main">
                    ¥{stock.targetPrice.toLocaleString()}
                  </Typography>
                </Box>
              )}
              {stock.stopLossPrice != null && (
                <Box>
                  <Typography variant="caption" color="text.secondary">損切りライン</Typography>
                  <Typography variant="h6" fontWeight="bold" color="error.main">
                    ¥{stock.stopLossPrice.toLocaleString()}
                  </Typography>
                </Box>
              )}
              {stock.supportPrice != null && (
                <Box>
                  <Typography variant="caption" color="text.secondary">支持線 (25日安値)</Typography>
                  <Typography variant="body1">¥{stock.supportPrice.toLocaleString()}</Typography>
                </Box>
              )}
              {stock.resistancePrice != null && (
                <Box>
                  <Typography variant="caption" color="text.secondary">抵抗線 (25日高値)</Typography>
                  <Typography variant="body1">¥{stock.resistancePrice.toLocaleString()}</Typography>
                </Box>
              )}
            </Box>
            {stock.activeSignals.length > 0 && (
              <Box mt={2} display="flex" gap={0.5} flexWrap="wrap">
                {stock.activeSignals.map((s: string) => (
                  <Chip key={s} label={s} size="small" variant="outlined"
                    color={stock.signal === 'buy' ? 'success' : stock.signal === 'sell' ? 'error' : 'default'} />
                ))}
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="subtitle1" fontWeight="bold">
              株価チャート
            </Typography>
            <ToggleButtonGroup
              value={period}
              exclusive
              onChange={(_, value) => value && setPeriod(value)}
              size="small"
            >
              <ToggleButton value="1m">1M</ToggleButton>
              <ToggleButton value="3m">3M</ToggleButton>
              <ToggleButton value="6m">6M</ToggleButton>
              <ToggleButton value="1y">1Y</ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {chartLoading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="close" stroke="#1976d2" name="終値" dot={false} />
                <Line type="monotone" dataKey="sma5" stroke="#4caf50" name="SMA5" dot={false} />
                <Line type="monotone" dataKey="sma25" stroke="#ff9800" name="SMA25" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            テクニカル指標
          </Typography>

          <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                RSI (14)
              </Typography>
              <Typography
                variant="h6"
                color={stock.rsi <= 30 ? 'success.main' : stock.rsi >= 70 ? 'error.main' : 'text.primary'}
              >
                {stock.rsi.toFixed(1)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {stock.rsi <= 30 ? '売られすぎ' : stock.rsi >= 70 ? '買われすぎ' : '中立'}
              </Typography>
            </Box>

            <Box>
              <Typography variant="caption" color="text.secondary">
                MACD
              </Typography>
              <Typography
                variant="h6"
                color={stock.macd > stock.macdSignal ? 'success.main' : 'error.main'}
              >
                {stock.macd.toFixed(2)}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                シグナル: {stock.macdSignal.toFixed(2)}
              </Typography>
            </Box>

            <Box>
              <Typography variant="caption" color="text.secondary">
                移動平均 (5日)
              </Typography>
              <Typography variant="h6">
                ¥{stock.sma5.toLocaleString()}
              </Typography>
            </Box>

            <Box>
              <Typography variant="caption" color="text.secondary">
                移動平均 (25日)
              </Typography>
              <Typography variant="h6">
                ¥{stock.sma25.toLocaleString()}
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
