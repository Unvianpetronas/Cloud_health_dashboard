# Frontend Components

Đây là thư viện components cho AWS Cloud Health Dashboard.

## 📁 Cấu trúc

```
components/
├── common/           # Components dùng chung
│   ├── Button.jsx    # Button với nhiều variants
│   ├── Card.jsx      # Card container
│   ├── Loading.jsx   # Loading spinner
│   ├── Header.jsx    # Header với navigation
│   └── ErrorBoundary.jsx # Error handling
├── dashboard/        # Components cho dashboard
│   ├── MetricsCard.jsx     # KPI metrics cards
│   ├── AlertsPanel.jsx     # Alerts management
│   └── ServiceStatusList.jsx # Service status
├── charts/           # Chart components
│   ├── CostChart.jsx        # Cost trends chart
│   ├── ServiceHealthChart.jsx # Health pie chart
│   └── PerformanceChart.jsx   # Performance metrics
└── index.js          # Export tất cả components
```

## 🎨 Design System

### Colors
- **Primary**: `#3b82f6` (blue-600)
- **Success**: `#10b981` (green-600)
- **Warning**: `#f59e0b` (yellow-500)
- **Error**: `#ef4444` (red-500)
- **Gray**: `#6b7280` (gray-500)

### Components

#### Button
```jsx
<Button variant="primary" size="md" loading={false}>
  Click me
</Button>
```

**Variants**: `primary`, `secondary`, `success`, `danger`, `outline`
**Sizes**: `sm`, `md`, `lg`

#### Card
```jsx
<Card padding="p-6" shadow="shadow-sm" hover={true}>
  Content here
</Card>
```

#### MetricsCard
```jsx
<MetricsCard
  title="Total Cost"
  value="$1,847"
  change="8.2% from last month"
  changeType="negative"
  icon={DollarSign}
  iconColor="#3b82f6"
  iconBgColor="#dbeafe"
/>
```

#### Charts
Tất cả charts sử dụng Recharts và có responsive design:

```jsx
<CostChart data={costsData} title="Custom Title" />
<ServiceHealthChart data={healthData} />
<PerformanceChart data={performanceData} />
```

## 🚀 Usage

### Import components
```jsx
import { Button, Card, MetricsCard } from '../components';
// hoặc
import Button from '../components/common/Button';
```

### Sử dụng trong pages
```jsx
import React from 'react';
import { MetricsCard, CostChart } from '../components';

const MyPage = () => {
  return (
    <div>
      <MetricsCard title="Example" value="123" />
      <CostChart data={myData} />
    </div>
  );
};
```

## 🔧 Development

### Thêm component mới
1. Tạo file trong thư mục phù hợp
2. Follow naming convention: `PascalCase.jsx`
3. Export trong `index.js`
4. Thêm documentation

### Best Practices
- Sử dụng TypeScript cho type safety (nếu migrate)
- Prop validation với PropTypes
- Responsive design với Tailwind
- Accessibility compliance
- Error boundaries cho error handling

## 📱 Responsive Design

Tất cả components được thiết kế responsive:
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px  
- **Desktop**: > 1024px

Grid system:
```jsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
```

## 🎯 Next Steps

1. **Add more components**: Modal, Dropdown, Tabs
2. **Theme system**: Dark/light mode support
3. **Animation**: Framer Motion integration
4. **Testing**: Jest + React Testing Library
5. **Storybook**: Component documentation
6. **TypeScript**: Type safety migration