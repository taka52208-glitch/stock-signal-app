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

function AppHeader() {
  const navigate = useNavigate();
  const location = useLocation();

  const showHeader = ['/', '/signals', '/portfolio', '/history'].includes(location.pathname);
  if (!showHeader) return null;

  const titles: Record<string, string> = {
    '/': 'おすすめ銘柄',
    '/signals': '全銘柄シグナル',
    '/portfolio': 'ポートフォリオ',
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

  const showNav = ['/', '/signals', '/portfolio', '/history'].includes(location.pathname);
  if (!showNav) return null;

  const pathToValue: Record<string, number> = { '/': 0, '/portfolio': 1, '/history': 2 };
  const valueToPath = ['/', '/portfolio', '/history'];

  return (
    <Paper sx={{ position: 'fixed', bottom: 0, left: 0, right: 0 }} elevation={3}>
      <BottomNavigation
        value={pathToValue[location.pathname] ?? 0}
        onChange={(_, newValue) => navigate(valueToPath[newValue])}
        showLabels
      >
        <BottomNavigationAction label="おすすめ" icon={<Recommend />} />
        <BottomNavigationAction label="保有株" icon={<AccountBalance />} />
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
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/history" element={<TransactionHistory />} />
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
