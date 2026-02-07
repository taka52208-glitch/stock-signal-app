import { Box, Typography } from '@mui/material';
import { Star, StarBorder } from '@mui/icons-material';

interface Props {
  strength: number;
  showLabel?: boolean;
}

const STRENGTH_LABELS = ['', '弱', '中', '強'];

export default function SignalStrengthDisplay({ strength, showLabel = true }: Props) {
  const label = STRENGTH_LABELS[strength] || '';

  return (
    <Box display="flex" alignItems="center" gap={0.25}>
      {[1, 2, 3].map((i) => (
        i <= strength
          ? <Star key={i} sx={{ fontSize: 16, color: 'warning.main' }} />
          : <StarBorder key={i} sx={{ fontSize: 16, color: 'grey.400' }} />
      ))}
      {showLabel && label && (
        <Typography variant="caption" color="text.secondary" ml={0.5}>
          {label}
        </Typography>
      )}
    </Box>
  );
}
