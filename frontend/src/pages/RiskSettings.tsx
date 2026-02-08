import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, IconButton, Card, CardContent, Button,
  Slider, Alert, Snackbar, CircularProgress,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { RiskRules } from '../types';

const DEFAULT_RULES: RiskRules = {
  maxPositionPercent: 30,
  maxLossPerTrade: 5,
  maxPortfolioLoss: 10,
  maxOpenPositions: 5,
};

export default function RiskSettings() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [rules, setRules] = useState<RiskRules>(DEFAULT_RULES);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const { data: savedRules, isLoading } = useQuery({
    queryKey: ['riskRules'],
    queryFn: api.getRiskRules,
  });

  useEffect(() => {
    if (savedRules) setRules(savedRules);
  }, [savedRules]);

  const mutation = useMutation({
    mutationFn: api.updateRiskRules,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['riskRules'] });
      setSnackbarOpen(true);
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
      <Box display="flex" alignItems="center" mb={2}>
        <IconButton onClick={() => navigate(-1)}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h6" fontWeight="bold" ml={1}>
          リスク管理設定
        </Typography>
      </Box>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            ポジション管理
          </Typography>

          <Box mb={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              1銘柄の最大ポートフォリオ比率: {rules.maxPositionPercent}%
            </Typography>
            <Slider
              value={rules.maxPositionPercent}
              onChange={(_, v) => setRules({ ...rules, maxPositionPercent: v as number })}
              min={5}
              max={100}
              step={5}
              marks
              valueLabelDisplay="auto"
            />
          </Box>

          <Box mb={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              最大保有銘柄数: {rules.maxOpenPositions}
            </Typography>
            <Slider
              value={rules.maxOpenPositions}
              onChange={(_, v) => setRules({ ...rules, maxOpenPositions: v as number })}
              min={1}
              max={20}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            損失管理
          </Typography>

          <Box mb={3}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              1取引の最大損失率: {rules.maxLossPerTrade}%
            </Typography>
            <Slider
              value={rules.maxLossPerTrade}
              onChange={(_, v) => setRules({ ...rules, maxLossPerTrade: v as number })}
              min={1}
              max={20}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
          </Box>

          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              ポートフォリオ最大損失率: {rules.maxPortfolioLoss}%
            </Typography>
            <Slider
              value={rules.maxPortfolioLoss}
              onChange={(_, v) => setRules({ ...rules, maxPortfolioLoss: v as number })}
              min={1}
              max={50}
              step={1}
              marks
              valueLabelDisplay="auto"
            />
          </Box>
        </CardContent>
      </Card>

      <Box display="flex" gap={2}>
        <Button variant="outlined" fullWidth onClick={() => setRules(DEFAULT_RULES)}>
          デフォルトに戻す
        </Button>
        <Button
          variant="contained"
          fullWidth
          onClick={() => mutation.mutate(rules)}
          disabled={mutation.isPending}
        >
          保存
        </Button>
      </Box>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={3000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert severity="success" onClose={() => setSnackbarOpen(false)}>
          リスク管理設定を保存しました
        </Alert>
      </Snackbar>
    </Box>
  );
}
