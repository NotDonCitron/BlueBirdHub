import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Mon', tasks: 4 },
  { name: 'Tue', tasks: 3 },
  { name: 'Wed', tasks: 5 },
  { name: 'Thu', tasks: 4 },
  { name: 'Fri', tasks: 6 },
  { name: 'Sat', tasks: 8 },
  { name: 'Sun', tasks: 7 },
];

const TaskCompletionLineChart = () => {
  return (
    <div className="chart-container">
      <h3>Tasks Completed This Week</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="tasks" stroke="#8884d8" activeDot={{ r: 8 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TaskCompletionLineChart; 