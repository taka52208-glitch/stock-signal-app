import { Badge } from '@mui/material';
import { Notifications } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';

export default function AlertBadge() {
  const { data } = useQuery({
    queryKey: ['unreadAlertCount'],
    queryFn: api.getUnreadAlertCount,
    refetchInterval: 30000,
  });

  return (
    <Badge badgeContent={data?.count || 0} color="error">
      <Notifications />
    </Badge>
  );
}
