import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppBar, Toolbar, Typography, IconButton, Box, Container, BottomNavigation, BottomNavigationAction, Paper } from '@mui/material';
import { Settings as SettingsIcon, Recommend, AccountBalance, History } from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

import Recommendations from './pages/Recommendations';
import StockList from './pages/StockList';
import StockDetail from './pages/StockDetail';
import Settings from './pages/Settings';
import Portfolio from './pages/Portfolio';
import TransactionHistory from './pages/TransactionHistory';
import Alerts from './pages/Alerts';
import RiskSettings from './pages/RiskSettings';
import BacktestList from './pages/BacktestList';
import BacktestCreate from './pages/BacktestCreate';
import BacktestDetail from './pages/BacktestDetail';
import BrokerageSetup from './pages/BrokerageSetup';
import BrokerageOrders from './pages/BrokerageOrders';
import AutoTradeSettings from './pages/AutoTradeSettings';
import AlertBadge from './components/AlertBadge';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1分
      retry: 1,
    },
  },
});

const NAV_PATHS = ['/', '/portfolio', '/alerts', '/history'];

function AppHeader() {
  const navigate = useNavigate();
  const location = useLocation();

  const showHeader = NAV_PATHS.includes(location.pathname);
  if (!showHeader) return null;

  const titles: Record<string, string> = {
    '/': 'おすすめ銘柄',
    '/signals': '全銘柄シグナル',
    '/portfolio': 'ポートフォリオ',
    '/alerts': 'アラート',
    '/history': '取引履歴',
  };

  return (
    <AppBar position="static" elevation={0}>
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {titles[location.pathname] || '株式シグナル'}
        </Typography>
        <IconButton color="inherit" onClick={() => navigate('/settings')}>
          <SettingsIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
}

function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();

  const showNav = NAV_PATHS.includes(location.pathname);
  if (!showNav) return null;

  const pathToValue: Record<string, number> = { '/': 0, '/portfolio': 1, '/alerts': 2, '/history': 3 };
  const valueToPath = ['/', '/portfolio', '/alerts', '/history'];

  return (
    <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0 }} elevation={3}>
      <BottomNavigation
        value={pathToValue[location.pathname] ?? 0}
        onChange={(_, newValue) => navigate(valueToPath[newValue])}
        showLabels
      >
        <BottomNavigationAction label="おすすめ" icon={<Recommend />} />
        <BottomNavigationAction label="保有株" icon={<AccountBalance />} />
        <BottomNavigationAction label="アラート" icon={<AlertBadge />} />
        <BottomNavigationAction label="履歴" icon={<History />} />
      </BottomNavigation>
    </Paper>
  );
}

function AppContent() {
  return (
    <>
      <AppHeader />
      <Container maxWidth="sm" disableGutters>
        <Box pb={10}>
          <Routes>
            <Route path="/" element={<Recommendations />} />
            <Route path="/signals" element={<StockList />} />
            <Route path="/stock/:code" element={<StockDetail />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/settings/risk" element={<RiskSettings />} />
            <Route path="/settings/brokerage" element={<BrokerageSetup />} />
            <Route path="/settings/auto-trade" element={<AutoTradeSettings />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/history" element={<TransactionHistory />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/backtests" element={<BacktestList />} />
            <Route path="/backtests/new" element={<BacktestCreate />} />
            <Route path="/backtests/:id" element={<BacktestDetail />} />
            <Route path="/orders" element={<BrokerageOrders />} />
          </Routes>
        </Box>
      </Container>
      <BottomNav />
    </>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
