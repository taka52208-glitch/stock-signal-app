import { useState } from 'react';
import {
  Box, Typography, Button, Dialog, DialogTitle, DialogContent, DialogActions, ToggleButton, ToggleButtonGroup,
  TextField,
} from '@mui/material';
import { Edit as EditIcon } from '@mui/icons-material';

const PRESETS = [50000, 100000, 300000, 500000, 1000000];

interface Props {
  budget: number;
  onBudgetChange: (budget: number) => void;
}

export default function BudgetSetting({ budget, onBudgetChange }: Props) {
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(budget);
  const [custom, setCustom] = useState('');
  const [useCustom, setUseCustom] = useState(false);

  const handleOpen = () => {
    setSelected(budget);
    setUseCustom(!PRESETS.includes(budget));
    setCustom(PRESETS.includes(budget) ? '' : String(budget));
    setOpen(true);
  };

  const handleSave = () => {
    const value = useCustom ? Number(custom) : selected;
    if (value >= 10000) {
      onBudgetChange(value);
      setOpen(false);
    }
  };

  return (
    <>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}
        sx={{ bgcolor: 'grey.50', p: 1.5, borderRadius: 1 }}>
        <Box>
          <Typography variant="caption" color="text.secondary">投資予算</Typography>
          <Typography variant="h6" fontWeight="bold">
            ¥{budget.toLocaleString()}
          </Typography>
        </Box>
        <Button size="small" variant="outlined" startIcon={<EditIcon />} onClick={handleOpen}>
          変更
        </Button>
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)} fullWidth maxWidth="xs">
        <DialogTitle>投資予算を設定</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" mb={2}>
            おすすめ銘柄の購入株数計算に使用されます
          </Typography>

          <ToggleButtonGroup
            value={useCustom ? null : selected}
            exclusive
            onChange={(_, val) => {
              if (val != null) {
                setSelected(val);
                setUseCustom(false);
              }
            }}
            sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}
          >
            {PRESETS.map((p) => (
              <ToggleButton key={p} value={p} sx={{ flex: '1 1 auto' }}>
                ¥{p.toLocaleString()}
              </ToggleButton>
            ))}
          </ToggleButtonGroup>

          <TextField
            label="カスタム金額"
            type="number"
            fullWidth
            size="small"
            value={custom}
            onChange={(e) => {
              setCustom(e.target.value);
              setUseCustom(true);
            }}
            placeholder="例: 200000"
            inputProps={{ min: 10000 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>キャンセル</Button>
          <Button variant="contained" onClick={handleSave}>設定</Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
