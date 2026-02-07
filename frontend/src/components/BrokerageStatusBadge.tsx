import { Chip } from '@mui/material';
import { Circle } from '@mui/icons-material';

interface Props {
  connected: boolean;
}

export default function BrokerageStatusBadge({ connected }: Props) {
  return (
    <Chip
      icon={<Circle sx={{ fontSize: 10 }} />}
      label={connected ? '接続中' : '未接続'}
      size="small"
      color={connected ? 'success' : 'default'}
      variant="outlined"
    />
  );
}
