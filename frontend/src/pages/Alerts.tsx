import { useState } from 'react';
import {
  Box, Typography, IconButton, Card, CardContent, Chip, Fab,
  Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField,
  ToggleButton, ToggleButtonGroup, CircularProgress, Alert, Tab, Tabs,
} from '@mui/material';
import { ArrowBack, Add, Delete } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import type { AlertType } from '../types';

const alertTypeLabels: Record<AlertType, string> = {
  price_above: '価格が以上',
  price_below: '価格が以下',
  signal_change: 'シグナル変化',
};

export default function Alerts() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState(0);
  const [openDialog, setOpenDialog] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    alertType: 'price_above' as AlertType,
    conditionValue: '',
  });

  const { data: alerts, isLoading: alertsLoading } = useQuery({
    queryKey: ['alerts'],
    queryFn: api.getAlerts,
  });

  const { data: history, isLoading: historyLoading } = useQuery({
    queryKey: ['alertHistory'],
    queryFn: api.getAlertHistory,
  });

  const createMutation = useMutation({
    mutationFn: api.createAlert,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
      setOpenDialog(false);
      setFormData({ code: '', alertType: 'price_above', conditionValue: '' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteAlert,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['alerts'] }),
  });

  const markReadMutation = useMutation({
    mutationFn: api.markAlertsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alertHistory'] });
      queryClient.invalidateQueries({ queryKey: ['unreadAlertCount'] });
    },
  });

  const handleCreate = () => {
    if (!formData.code.match(/^\d{4}$/)) return;
    createMutation.mutate({
      code: formData.code,
      alertType: formData.alertType,
      conditionValue: formData.alertType !== 'signal_change' ? parseFloat(formData.conditionValue) : undefined,
    });
  };

  const handleMarkAllRead = () => {
    const unreadIds = history?.filter(h => !h.isRead).map(h => h.id) || [];
    if (unreadIds.length > 0) {
      markReadMutation.mutate(unreadIds);
    }
  };

  const isLoading = alertsLoading || historyLoading;

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
          アラート
        </Typography>
      </Box>

      <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={{ mb: 2 }}>
        <Tab label={`設定 (${alerts?.length || 0})`} />
        <Tab label={`履歴 (${history?.filter(h => !h.isRead).length || 0})`} />
      </Tabs>

      {tab === 0 && (
        <>
          {alerts?.length === 0 ? (
            <Alert severity="info">
              アラートが設定されていません。右下の＋ボタンから追加してください。
            </Alert>
          ) : (
            alerts?.map((alert) => (
              <Card key={alert.id} sx={{ mb: 1 }}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center">
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        {alert.code} - {alert.name}
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                        <Chip
                          label={alertTypeLabels[alert.alertType as AlertType]}
                          size="small"
                          color={alert.isActive ? 'primary' : 'default'}
                        />
                        {alert.conditionValue != null && (
                          <Typography variant="body2" fontWeight="bold">
                            ¥{alert.conditionValue.toLocaleString()}
                          </Typography>
                        )}
                        {!alert.isActive && (
                          <Chip label="無効" size="small" color="default" variant="outlined" />
                        )}
                      </Box>
                    </Box>
                    <IconButton size="small" onClick={() => deleteMutation.mutate(alert.id)}>
                      <Delete fontSize="small" />
                    </IconButton>
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </>
      )}

      {tab === 1 && (
        <>
          {history && history.filter(h => !h.isRead).length > 0 && (
            <Box mb={2}>
              <Button size="small" onClick={handleMarkAllRead}>
                すべて既読にする
              </Button>
            </Box>
          )}
          {history?.length === 0 ? (
            <Alert severity="info">アラート履歴がありません</Alert>
          ) : (
            history?.map((h) => (
              <Card key={h.id} sx={{ mb: 1, opacity: h.isRead ? 0.7 : 1 }}>
                <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                    <Box>
                      <Typography variant="body2" fontWeight={h.isRead ? 'normal' : 'bold'}>
                        {h.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {new Date(h.triggeredAt).toLocaleString('ja-JP')}
                      </Typography>
                    </Box>
                    {!h.isRead && (
                      <Chip label="NEW" size="small" color="error" />
                    )}
                  </Box>
                </CardContent>
              </Card>
            ))
          )}
        </>
      )}

      <Fab
        color="primary"
        sx={{ position: 'fixed', bottom: 72, right: 16 }}
        onClick={() => setOpenDialog(true)}
      >
        <Add />
      </Fab>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} fullWidth maxWidth="xs">
        <DialogTitle>アラートを追加</DialogTitle>
        <DialogContent>
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
            value={formData.alertType}
            exclusive
            onChange={(_, v) => v && setFormData({ ...formData, alertType: v })}
            fullWidth
            sx={{ my: 2 }}
            size="small"
          >
            <ToggleButton value="price_above">価格以上</ToggleButton>
            <ToggleButton value="price_below">価格以下</ToggleButton>
            <ToggleButton value="signal_change">シグナル変化</ToggleButton>
          </ToggleButtonGroup>
          {formData.alertType !== 'signal_change' && (
            <TextField
              label="条件価格（円）"
              type="number"
              fullWidth
              margin="dense"
              value={formData.conditionValue}
              onChange={(e) => setFormData({ ...formData, conditionValue: e.target.value })}
              inputProps={{ min: 0 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>キャンセル</Button>
          <Button
            onClick={handleCreate}
            variant="contained"
            disabled={
              !formData.code.match(/^\d{4}$/) ||
              (formData.alertType !== 'signal_change' && !formData.conditionValue) ||
              createMutation.isPending
            }
          >
            追加
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
