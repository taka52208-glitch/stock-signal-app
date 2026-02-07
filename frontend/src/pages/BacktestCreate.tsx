import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box, Typography, IconButton, Card, CardContent, TextField, Button,
  Chip, CircularProgress, Alert,
} from '@mui/material';
import { ArrowBack } from '@mui/icons-material';
import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../api/client';

export default function BacktestCreate() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: '',
    startDate: '',
    endDate: '',
    initialCapital: '1000000',
    codeInput: '',
  });
  const [codes, setCodes] = useState<string[]>([]);

  const { data: stocks } = useQuery({
    queryKey: ['stocks'],
    queryFn: api.getStocks,
  });

  const mutation = useMutation({
    mutationFn: api.createBacktest,
    onSuccess: (data) => {
      navigate(`/backtests/${data.id}`);
    },
  });

  const addCode = () => {
    const code = formData.codeInput.trim();
    if (code.match(/^\d{4}$/) && !codes.includes(code)) {
      setCodes([...codes, code]);
      setFormData({ ...formData, codeInput: '' });
    }
  };

  const removeCode = (code: string) => {
    setCodes(codes.filter((c) => c !== code));
  };

  const addAllStocks = () => {
    if (stocks) {
      const newCodes = stocks.map((s) => s.code).filter((c) => !codes.includes(c));
      setCodes([...codes, ...newCodes]);
    }
  };

  const handleSubmit = () => {
    if (!formData.name || !formData.startDate || !formData.endDate || codes.length === 0) return;
    mutation.mutate({
      name: formData.name,
      startDate: formData.startDate,
      endDate: formData.endDate,
      initialCapital: parseFloat(formData.initialCapital),
      codes,
    });
  };

  return (
    <Box p={2}>
      <Box display="flex" alignItems="center" mb={2}>
        <IconButton onClick={() => navigate(-1)}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h6" fontWeight="bold" ml={1}>
          バックテスト作成
        </Typography>
      </Box>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            基本設定
          </Typography>
          <TextField
            label="テスト名"
            fullWidth
            margin="dense"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
          <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mt={1}>
            <TextField
              label="開始日"
              type="date"
              fullWidth
              margin="dense"
              value={formData.startDate}
              onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              label="終了日"
              type="date"
              fullWidth
              margin="dense"
              value={formData.endDate}
              onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Box>
          <TextField
            label="初期資金（円）"
            type="number"
            fullWidth
            margin="dense"
            value={formData.initialCapital}
            onChange={(e) => setFormData({ ...formData, initialCapital: e.target.value })}
            inputProps={{ min: 10000 }}
          />
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" fontWeight="bold" mb={2}>
            対象銘柄
          </Typography>
          <Box display="flex" gap={1} mb={2}>
            <TextField
              label="銘柄コード（4桁）"
              size="small"
              value={formData.codeInput}
              onChange={(e) => setFormData({ ...formData, codeInput: e.target.value })}
              inputProps={{ maxLength: 4 }}
              onKeyDown={(e) => e.key === 'Enter' && addCode()}
            />
            <Button variant="outlined" onClick={addCode} size="small">
              追加
            </Button>
            {stocks && stocks.length > 0 && (
              <Button variant="text" onClick={addAllStocks} size="small">
                監視銘柄を全追加
              </Button>
            )}
          </Box>
          <Box display="flex" gap={0.5} flexWrap="wrap">
            {codes.map((code) => (
              <Chip key={code} label={code} onDelete={() => removeCode(code)} size="small" />
            ))}
          </Box>
          {codes.length === 0 && (
            <Typography variant="caption" color="text.secondary">
              銘柄を追加してください
            </Typography>
          )}
        </CardContent>
      </Card>

      {mutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          バックテストの作成に失敗しました
        </Alert>
      )}

      <Button
        variant="contained"
        fullWidth
        size="large"
        onClick={handleSubmit}
        disabled={
          !formData.name || !formData.startDate || !formData.endDate ||
          codes.length === 0 || mutation.isPending
        }
        startIcon={mutation.isPending ? <CircularProgress size={20} /> : undefined}
      >
        {mutation.isPending ? '実行中...' : 'バックテストを実行'}
      </Button>
    </Box>
  );
}
