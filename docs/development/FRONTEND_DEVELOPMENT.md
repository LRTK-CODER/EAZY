# Frontend 개발 가이드 (Frontend Development)

[← 메인 문서로 돌아가기](../README.md)

**작성일**: 2026-01-09
**대상 독자**: Frontend 개발자

---

## 목차

- [코딩 스타일](#코딩-스타일)
- [파일 명명 규칙](#파일-명명-규칙)
- [컴포넌트 구조 (Atomic Design)](#컴포넌트-구조-atomic-design)
- [Presentation & Container 패턴](#presentation--container-패턴)
- [주요 기능 구현 가이드](#주요-기능-구현-가이드)
  - [프로젝트 관리](#프로젝트-관리)
  - [Target 관리](#target-관리)
  - [스캔 결과 추적 (TanStack Query 폴링)](#스캔-결과-추적-tanstack-query-폴링)
- [보안 규칙](#보안-규칙)
- [성능 최적화](#성능-최적화)
- [접근성 (Accessibility)](#접근성-accessibility)

---

## 코딩 스타일

EAZY Frontend는 React 및 TypeScript 표준 스타일을 따릅니다.

### 도구

| 도구 | 용도 | 실행 명령 |
|------|------|----------|
| **Prettier** | 코드 포맷터 (2 spaces) | `npm run format` |
| **ESLint** | 린터 | `npm run lint` |
| **TypeScript** | 타입 체크 (Strict Mode) | `npm run type-check` |

### 스타일 가이드

1. **들여쓰기**: 2 spaces
2. **따옴표**: 작은따옴표 (`'`) 사용
3. **세미콜론**: 사용하지 않음 (Prettier 기본값)
4. **최대 줄 길이**: 80자
5. **Import 순서**: React → 서드파티 → 로컬
6. **Naming Conventions**:
   - 컴포넌트: `PascalCase`
   - 함수/변수: `camelCase`
   - 상수: `UPPER_SNAKE_CASE`
   - CSS 클래스: `kebab-case` (TailwindCSS)

### 코드 포맷팅 예시

```bash
# 1. Prettier 실행 (자동 포맷팅)
cd frontend
npm run format

# 2. ESLint 실행 (린팅)
npm run lint

# 3. TypeScript 체크
npm run type-check
```

---

## 파일 명명 규칙

| 파일 유형 | 규칙 | 예시 |
|----------|------|------|
| **컴포넌트** | PascalCase | `CreateProjectForm.tsx` |
| **페이지** | PascalCase | `ProjectDetailPage.tsx` |
| **Hook** | camelCase (use 접두사) | `useProjects.ts` |
| **Service** | camelCase | `projectService.ts` |
| **Type** | camelCase | `project.ts` |
| **Util** | camelCase | `dateUtils.ts` |
| **shadcn Hook** | kebab-case | `use-mobile.tsx` |

### 디렉토리 구조

```
src/
├── components/
│   ├── ui/                        # Atoms (shadcn/ui)
│   │   ├── button.tsx
│   │   ├── dialog.tsx
│   │   └── input.tsx
│   ├── features/                  # Molecules/Organisms
│   │   ├── project/
│   │   │   ├── CreateProjectForm.tsx
│   │   │   └── ProjectFormFields.tsx
│   │   └── target/
│   │       ├── TargetList.tsx
│   │       └── CreateTargetForm.tsx
│   └── layout/                    # Templates
│       ├── MainLayout.tsx
│       ├── Header.tsx
│       └── Sidebar.tsx
│
├── pages/                         # Pages
│   ├── ProjectsPage.tsx
│   └── ProjectDetailPage.tsx
│
├── hooks/                         # Custom Hooks
│   ├── useProjects.ts
│   └── useTargets.ts
│
├── services/                      # API 클라이언트
│   ├── projectService.ts
│   └── targetService.ts
│
├── types/                         # TypeScript 타입
│   ├── project.ts
│   └── target.ts
│
├── schemas/                       # Zod 스키마
│   ├── projectSchema.ts
│   └── targetSchema.ts
│
└── lib/                           # 유틸리티
    ├── api.ts
    └── utils.ts
```

---

## 컴포넌트 구조 (Atomic Design)

EAZY Frontend는 **Atomic Design** 방법론을 따릅니다.

### Atomic Design 계층

```
Atoms (원자)
  ↓
Molecules (분자)
  ↓
Organisms (유기체)
  ↓
Templates (템플릿)
  ↓
Pages (페이지)
```

### 예시: CreateProjectForm

```
Pages (ProjectsPage.tsx)
  └── Templates (MainLayout.tsx)
      └── Organisms (CreateProjectForm.tsx)
          └── Molecules (ProjectFormFields.tsx)
              └── Atoms (Button, Input, Textarea)
```

### 1. Atoms (ui/)

**shadcn/ui 컴포넌트** (재사용 가능한 기본 UI 요소)

```typescript
// src/components/ui/button.tsx

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          'inline-flex items-center justify-center rounded-md font-medium',
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

export { Button }
```

### 2. Molecules (features/)

**비즈니스 로직이 없는 재사용 가능한 컴포넌트**

```typescript
// src/components/features/project/ProjectFormFields.tsx

import { UseFormReturn } from 'react-hook-form'
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { ProjectFormValues } from '@/schemas/projectSchema'

interface ProjectFormFieldsProps {
  form: UseFormReturn<ProjectFormValues>
}

export function ProjectFormFields({ form }: ProjectFormFieldsProps) {
  return (
    <>
      <FormField
        name="name"
        control={form.control}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl>
              <Input placeholder="Project name" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        name="description"
        control={form.control}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Description</FormLabel>
            <FormControl>
              <Textarea
                placeholder="Project description (optional)"
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  )
}
```

### 3. Organisms (features/)

**비즈니스 로직을 포함한 컴포넌트**

```typescript
// src/components/features/project/CreateProjectForm.tsx

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Form } from '@/components/ui/form'
import { ProjectFormFields } from './ProjectFormFields'
import { useCreateProject } from '@/hooks/useProjects'
import { projectFormSchema, ProjectFormValues } from '@/schemas/projectSchema'

export function CreateProjectForm() {
  const [open, setOpen] = useState(false)
  const createProject = useCreateProject()

  const form = useForm<ProjectFormValues>({
    resolver: zodResolver(projectFormSchema),
    defaultValues: {
      name: '',
      description: ''
    }
  })

  const onSubmit = async (data: ProjectFormValues) => {
    await createProject.mutateAsync(data)
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Create Project</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create New Project</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <ProjectFormFields form={form} />
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? 'Creating...' : 'Create'}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

### 4. Templates (layout/)

**페이지 레이아웃 구조**

```typescript
// src/components/layout/MainLayout.tsx

import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function MainLayout() {
  return (
    <div className="grid h-screen grid-cols-[240px_1fr]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="flex flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
```

### 5. Pages (pages/)

**라우팅 페이지**

```typescript
// src/pages/ProjectsPage.tsx

import { CreateProjectForm } from '@/components/features/project/CreateProjectForm'
import { useProjects } from '@/hooks/useProjects'

export function ProjectsPage() {
  const { data: projects, isLoading } = useProjects({ archived: false })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Projects</h1>
        <CreateProjectForm />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {projects?.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  )
}
```

---

## Presentation & Container 패턴

**로직(Hooks)과 뷰(JSX)를 분리**하여 재사용성과 테스트 가능성을 높입니다.

### ✅ Good: Presentation & Container 분리

#### Container (로직 포함)

```typescript
// src/components/features/target/CreateTargetForm.tsx (Container)

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Form } from '@/components/ui/form'
import { TargetFormFields } from './TargetFormFields'
import { useCreateTarget } from '@/hooks/useTargets'
import { targetFormSchema, TargetFormValues } from '@/schemas/targetSchema'

interface CreateTargetFormProps {
  projectId: number
}

export function CreateTargetForm({ projectId }: CreateTargetFormProps) {
  const [open, setOpen] = useState(false)
  const createTarget = useCreateTarget(projectId)

  const form = useForm<TargetFormValues>({
    resolver: zodResolver(targetFormSchema),
    defaultValues: {
      name: '',
      url: '',
      scope: 'DOMAIN',
      description: ''
    }
  })

  const onSubmit = async (data: TargetFormValues) => {
    await createTarget.mutateAsync(data)
    setOpen(false)
    form.reset()
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Add Target</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add New Target</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <TargetFormFields form={form} />
            <Button type="submit" disabled={createTarget.isPending}>
              {createTarget.isPending ? 'Adding...' : 'Add Target'}
            </Button>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

#### Presentation (뷰만 담당)

```typescript
// src/components/features/target/TargetFormFields.tsx (Presentation)

import { UseFormReturn } from 'react-hook-form'
import {
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormMessage
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select'
import { TargetFormValues } from '@/schemas/targetSchema'

interface TargetFormFieldsProps {
  form: UseFormReturn<TargetFormValues>
}

export function TargetFormFields({ form }: TargetFormFieldsProps) {
  return (
    <>
      <FormField
        name="name"
        control={form.control}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Name</FormLabel>
            <FormControl>
              <Input placeholder="Target name" {...field} />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        name="url"
        control={form.control}
        render={({ field }) => (
          <FormItem>
            <FormLabel>URL</FormLabel>
            <FormControl>
              <Input
                type="url"
                placeholder="https://example.com"
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        name="scope"
        control={form.control}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Scope</FormLabel>
            <Select onValueChange={field.onChange} defaultValue={field.value}>
              <FormControl>
                <SelectTrigger>
                  <SelectValue placeholder="Select scope" />
                </SelectTrigger>
              </FormControl>
              <SelectContent>
                <SelectItem value="DOMAIN">Domain (전체 도메인)</SelectItem>
                <SelectItem value="SUBDOMAIN">Subdomain (서브도메인만)</SelectItem>
                <SelectItem value="URL_ONLY">URL Only (단일 URL)</SelectItem>
              </SelectContent>
            </Select>
            <FormMessage />
          </FormItem>
        )}
      />

      <FormField
        name="description"
        control={form.control}
        render={({ field }) => (
          <FormItem>
            <FormLabel>Description</FormLabel>
            <FormControl>
              <Textarea
                placeholder="Target description (optional)"
                {...field}
              />
            </FormControl>
            <FormMessage />
          </FormItem>
        )}
      />
    </>
  )
}
```

### ❌ Bad: 로직과 뷰 혼재

```typescript
// 안티패턴: 로직과 뷰가 분리되지 않아 재사용 불가

export function CreateTargetForm({ projectId }: CreateTargetFormProps) {
  // ... (로직)

  return (
    <Dialog>
      <DialogContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            {/* 폼 필드가 직접 작성되어 재사용 불가 */}
            <FormField name="name" ... />
            <FormField name="url" ... />
            <FormField name="scope" ... />
            <FormField name="description" ... />
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
```

---

## 주요 기능 구현 가이드

### 프로젝트 관리

#### 1. Custom Hook (TanStack Query)

```typescript
// src/hooks/useProjects.ts

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import * as projectService from '@/services/projectService'
import type { ProjectCreate, ProjectUpdate } from '@/types/project'

// Query Keys
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters: { archived?: boolean }) =>
    [...projectKeys.lists(), filters] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: number) => [...projectKeys.details(), id] as const
}

// Queries
export function useProjects(filters: { archived?: boolean } = {}) {
  return useQuery({
    queryKey: projectKeys.list(filters),
    queryFn: () => projectService.getProjects(filters)
  })
}

export function useProject(id: number) {
  return useQuery({
    queryKey: projectKeys.detail(id),
    queryFn: () => projectService.getProject(id),
    enabled: !!id
  })
}

// Mutations
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProjectCreate) => projectService.createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    }
  })
}

export function useUpdateProject(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProjectUpdate) =>
      projectService.updateProject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(id) })
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    }
  })
}

export function useArchiveProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => projectService.deleteProject(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    }
  })
}
```

#### 2. API Service

```typescript
// src/services/projectService.ts

import { api } from '@/lib/api'
import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project'

export async function getProjects(filters: {
  archived?: boolean
} = {}): Promise<Project[]> {
  const params = new URLSearchParams()
  if (filters.archived !== undefined) {
    params.append('archived', filters.archived.toString())
  }

  const response = await api.get(`/projects/?${params.toString()}`)
  return response.data
}

export async function getProject(id: number): Promise<Project> {
  const response = await api.get(`/projects/${id}`)
  return response.data
}

export async function createProject(data: ProjectCreate): Promise<Project> {
  const response = await api.post('/projects/', data)
  return response.data
}

export async function updateProject(
  id: number,
  data: ProjectUpdate
): Promise<Project> {
  const response = await api.patch(`/projects/${id}`, data)
  return response.data
}

export async function deleteProject(id: number): Promise<void> {
  await api.delete(`/projects/${id}`)
}
```

### Target 관리

#### Zod 스키마 유효성 검증

```typescript
// src/schemas/targetSchema.ts

import { z } from 'zod'

export const targetFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  url: z.string().url('Invalid URL'),
  scope: z.enum(['DOMAIN', 'SUBDOMAIN', 'URL_ONLY']),
  description: z.string().max(1000).optional()
})

export type TargetFormValues = z.infer<typeof targetFormSchema>
```

### 스캔 결과 추적 (TanStack Query 폴링)

#### Task 상태 폴링

```typescript
// src/hooks/useTasks.ts

import { useQuery } from '@tanstack/react-query'
import * as taskService from '@/services/taskService'

export const taskKeys = {
  all: ['tasks'] as const,
  details: () => [...taskKeys.all, 'detail'] as const,
  detail: (id: number) => [...taskKeys.details(), id] as const
}

export function useTaskStatus(taskId: number | null) {
  return useQuery({
    queryKey: taskKeys.detail(taskId!),
    queryFn: () => taskService.getTaskStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const data = query.state.data

      // Task가 없으면 폴링 안함
      if (!data) return false

      // COMPLETED 또는 FAILED 상태면 폴링 중지
      if (data.status === 'COMPLETED' || data.status === 'FAILED') {
        return false
      }

      // PENDING 또는 RUNNING 상태면 5초마다 폴링
      return 5000
    }
  })
}
```

#### UI 피드백 컴포넌트

```typescript
// src/components/features/target/ScanStatusBadge.tsx

import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'
import type { TaskStatus } from '@/types/task'

interface ScanStatusBadgeProps {
  status: TaskStatus
}

export function ScanStatusBadge({ status }: ScanStatusBadgeProps) {
  switch (status) {
    case 'PENDING':
      return (
        <Badge variant="secondary" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Pending
        </Badge>
      )
    case 'RUNNING':
      return (
        <Badge variant="default" className="gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Running
        </Badge>
      )
    case 'COMPLETED':
      return <Badge variant="success">Completed</Badge>
    case 'FAILED':
      return <Badge variant="destructive">Failed</Badge>
    default:
      return null
  }
}
```

#### TargetList with Scan Trigger

```typescript
// src/components/features/target/TargetList.tsx

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ScanStatusBadge } from './ScanStatusBadge'
import { useTriggerScan, useTargets } from '@/hooks/useTargets'
import { useTaskStatus } from '@/hooks/useTasks'

interface TargetListProps {
  projectId: number
}

export function TargetList({ projectId }: TargetListProps) {
  const { data: targets } = useTargets(projectId)
  const triggerScan = useTriggerScan(projectId)
  const [activeTaskId, setActiveTaskId] = useState<number | null>(null)

  // Task 상태 폴링 (5초 간격)
  const { data: task } = useTaskStatus(activeTaskId)

  const handleScan = async (targetId: number) => {
    const response = await triggerScan.mutateAsync(targetId)
    setActiveTaskId(response.task_id)
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>URL</TableHead>
          <TableHead>Scope</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {targets?.map((target) => (
          <TableRow key={target.id}>
            <TableCell>{target.name}</TableCell>
            <TableCell>{target.url}</TableCell>
            <TableCell>{target.scope}</TableCell>
            <TableCell>
              {task && <ScanStatusBadge status={task.status} />}
            </TableCell>
            <TableCell>
              <Button
                size="sm"
                onClick={() => handleScan(target.id)}
                disabled={triggerScan.isPending || task?.status === 'RUNNING'}
              >
                {triggerScan.isPending ? 'Starting...' : 'Scan'}
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
```

---

## 보안 규칙

### 1. XSS 방지

React는 기본적으로 **XSS를 방지**합니다. `dangerouslySetInnerHTML` 사용을 **절대 금지**합니다.

```typescript
// ✅ Good: React가 자동으로 이스케이프 처리
function ProjectCard({ project }: { project: Project }) {
  return <div>{project.name}</div>
}


// ❌ Bad: XSS 위험
function ProjectCard({ project }: { project: Project }) {
  return (
    <div dangerouslySetInnerHTML={{ __html: project.name }} />
  )
}
```

### 2. Input Validation (Zod)

**Zod**를 사용하여 입력 데이터를 검증합니다.

```typescript
import { z } from 'zod'

export const targetFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  url: z.string().url('Invalid URL'),
  scope: z.enum(['DOMAIN', 'SUBDOMAIN', 'URL_ONLY']),
  description: z.string().max(1000).optional()
})
```

### 3. 환경 변수 보안

`.env` 파일을 Git에서 제외하고, 민감한 정보는 환경 변수로 관리합니다.

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

```typescript
// src/lib/api.ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
```

---

## 성능 최적화

### 1. React.memo (불필요한 리렌더링 방지)

```typescript
import { memo } from 'react'

export const ProjectCard = memo(function ProjectCard({ project }: ProjectCardProps) {
  return (
    <div>
      <h3>{project.name}</h3>
      <p>{project.description}</p>
    </div>
  )
})
```

### 2. useCallback (함수 메모이제이션)

```typescript
import { useCallback } from 'react'

function TargetList({ projectId }: TargetListProps) {
  const handleScan = useCallback(
    async (targetId: number) => {
      await triggerScan.mutateAsync(targetId)
    },
    [triggerScan]
  )

  return (
    <Table>
      {targets?.map((target) => (
        <TableRow key={target.id}>
          <Button onClick={() => handleScan(target.id)}>Scan</Button>
        </TableRow>
      ))}
    </Table>
  )
}
```

### 3. TanStack Query 캐싱

```typescript
// 캐시 설정
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5분
      cacheTime: 10 * 60 * 1000 // 10분
    }
  }
})
```

---

## 접근성 (Accessibility)

### 1. ARIA Attributes

```typescript
<button aria-label="Create project">
  <Plus className="h-4 w-4" />
</button>
```

### 2. Keyboard Navigation

```typescript
<Dialog>
  <DialogTrigger asChild>
    <Button>Open Dialog</Button>
  </DialogTrigger>
  <DialogContent>
    {/* ESC 키로 닫기 가능 */}
  </DialogContent>
</Dialog>
```

### 3. Semantic HTML

```typescript
// ✅ Good: Semantic HTML
<nav>
  <ul>
    <li><Link to="/projects">Projects</Link></li>
    <li><Link to="/dashboard">Dashboard</Link></li>
  </ul>
</nav>

// ❌ Bad: Non-semantic
<div>
  <div onClick={...}>Projects</div>
  <div onClick={...}>Dashboard</div>
</div>
```

---

## 참고 자료

- [React 공식 문서](https://react.dev/)
- [TanStack Query 공식 문서](https://tanstack.com/query/latest)
- [shadcn/ui 공식 문서](https://ui.shadcn.com/)
- [Zod 공식 문서](https://zod.dev/)
- [TDD Guide (TDD_GUIDE.md)](./TDD_GUIDE.md)
- [Testing Strategy (TESTING_STRATEGY.md)](./TESTING_STRATEGY.md)
- [Backend Development Guide (BACKEND_DEVELOPMENT.md)](./BACKEND_DEVELOPMENT.md)

---

**다음 문서**: [Deployment Guide (DEPLOYMENT.md)](./DEPLOYMENT.md)
