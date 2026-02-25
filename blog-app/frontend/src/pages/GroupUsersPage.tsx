import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Avatar,
  Divider,
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { DataGrid, type GridColDef, type GridRenderCellParams } from '@mui/x-data-grid';
import { useAppSelector } from '../store/hooks';
import { dashboardApi, type GroupUser } from '../services/dashboardAPI';
import * as styles from './GroupUsersPageStyles';

const GroupUsersPage: React.FC = () => {
  const { user: currentUser } = useAppSelector((state) => state.auth);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string>('');
  const [users, setUsers] = useState<GroupUser[]>([]);

  const fetchUsers = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError('');
      const data = await dashboardApi.getGroupUsers();
      setUsers(data);
    } catch (err) {
      console.error('Error fetching group users:', err);
      setError('Failed to load group users. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const columns: GridColDef[] = [
    {
      field: 'username',
      headerName: 'Username',
      flex: 1,
      renderCell: (params: GridRenderCellParams) => {
        const isCurrentUser = params.row.id === currentUser?.id;
        return (
          <Box sx={styles.avatarCell}>
            <Avatar sx={styles.avatarSx(isCurrentUser)}>
              {(params.value as string).charAt(0).toUpperCase()}
            </Avatar>
            <Typography variant="body2" sx={styles.usernameSx(isCurrentUser)}>
              {params.value as string}
              {isCurrentUser && ' (you)'}
            </Typography>
          </Box>
        );
      },
    },
    {
      field: 'email',
      headerName: 'Email',
      flex: 1.5,
    },
    {
      field: 'created_at',
      headerName: 'Joined',
      flex: 1,
      valueFormatter: (value: string) =>
        new Date(value).toLocaleDateString(undefined, {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
        }),
    },
    {
      field: 'published_posts',
      headerName: 'Published Posts',
      flex: 0.75,
      type: 'number',
    },
  ];

  if (loading) {
    return (
      <Box sx={styles.loadingContainer}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={styles.pageContainer}>
      {error && (
        <Alert severity="error" sx={styles.errorAlert} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Paper sx={styles.paper}>
        <Box sx={styles.headerRow}>
          <Typography variant="h6">
            Group Members — {currentUser?.tenant_name}
          </Typography>
          <Button
            variant="outlined"
            size="small"
            startIcon={refreshing ? <CircularProgress size={16} /> : <Refresh />}
            onClick={() => fetchUsers(true)}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </Box>
        <Divider sx={styles.divider} />
        <Box sx={styles.dataGridWrapper}>
          <DataGrid
            rows={users}
            columns={columns}
            initialState={{
              pagination: { paginationModel: { pageSize: 25 } },
            }}
            pageSizeOptions={[10, 25, 50]}
            disableRowSelectionOnClick
            autoHeight
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default GroupUsersPage;
