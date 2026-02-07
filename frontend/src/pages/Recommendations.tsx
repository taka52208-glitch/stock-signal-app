import { useNavigate } from 'react-router-dom';
import { Box, Typography, CircularProgress, Alert, Button, Divider } from '@mui/material';
import { ArrowForward, HourglassEmpty } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import BuyRecommendationCard from '../components/BuyRecommendationCard';
import SellRecommendationCard from '../components/SellRecommendationCard';
import BudgetSetting from '../components/BudgetSetting';

export default function Recommendations() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['recommendations'],
    queryFn: api.getRecommendations,
  });

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: api.getSettings,
  });

  const budgetMutation = useMutation({
    mutationFn: (budget: number) => api.updateSettings({ ...settings!, investmentBudget: budget }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      queryClient.invalidateQueries({ queryKey: ['recommendations'] });
    },
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={2}>
        <Alert severity="error">データの取得に失敗しました</Alert>
      </Box>
    );
  }

  const buyRecs = data?.buyRecommendations || [];
  const sellRecs = data?.sellRecommendations || [];
  const budget = settings?.investmentBudget || data?.investmentBudget || 100000;

  return (
    <Box p={2}>
      <BudgetSetting budget={budget} onBudgetChange={(b) => budgetMutation.mutate(b)} />

      <Typography variant="subtitle1" fontWeight="bold" color="success.main" mb={1}>
        今が買い時
      </Typography>
      <Divider sx={{ mb: 1.5 }} />

      {buyRecs.length > 0 ? (
        buyRecs.map((rec) => <BuyRecommendationCard key={rec.code} recommendation={rec} />)
      ) : (
        <Alert severity="info" icon={<HourglassEmpty />} sx={{ mb: 2 }}>
          現在、買いシグナルの銘柄はありません
        </Alert>
      )}

      <Typography variant="subtitle1" fontWeight="bold" color="error.main" mt={2} mb={1}>
        売り時の銘柄
      </Typography>
      <Divider sx={{ mb: 1.5 }} />

      {sellRecs.length > 0 ? (
        sellRecs.map((rec) => <SellRecommendationCard key={rec.code} recommendation={rec} />)
      ) : (
        <Alert severity="info" icon={<HourglassEmpty />} sx={{ mb: 2 }}>
          現在、売りシグナルの銘柄はありません
        </Alert>
      )}

      <Box mt={3} textAlign="center">
        <Button
          variant="outlined"
          endIcon={<ArrowForward />}
          onClick={() => navigate('/signals')}
        >
          全銘柄を見る
        </Button>
      </Box>
    </Box>
  );
}
