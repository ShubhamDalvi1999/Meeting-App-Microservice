# 3. Forms and Validation

## Overview
This document covers form handling and validation patterns in our React application. These concepts build upon component basics and state management.

## Form Structure

### 1. Controlled Components
Basic form with controlled inputs:

```typescript
interface MeetingFormData {
    title: string;
    description: string;
    startTime: string;
    endTime: string;
    maxParticipants: number;
}

function MeetingForm({ onSubmit }: { onSubmit: (data: MeetingFormData) => void }) {
    const [formData, setFormData] = useState<MeetingFormData>({
        title: '',
        description: '',
        startTime: '',
        endTime: '',
        maxParticipants: 10
    });

    const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = (e: FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    return (
        <form onSubmit={handleSubmit}>
            <div className="form-group">
                <label htmlFor="title">Title</label>
                <input
                    id="title"
                    name="title"
                    value={formData.title}
                    onChange={handleChange}
                    required
                />
            </div>
            {/* Other form fields */}
        </form>
    );
}
```

### 2. Form Components
Reusable form components:

```typescript
interface InputFieldProps {
    label: string;
    name: string;
    value: string;
    onChange: (e: ChangeEvent<HTMLInputElement>) => void;
    error?: string;
    required?: boolean;
    type?: string;
}

function InputField({
    label,
    name,
    value,
    onChange,
    error,
    required = false,
    type = 'text'
}: InputFieldProps) {
    return (
        <div className={`form-field ${error ? 'has-error' : ''}`}>
            <label htmlFor={name}>
                {label}
                {required && <span className="required">*</span>}
            </label>
            <input
                id={name}
                name={name}
                type={type}
                value={value}
                onChange={onChange}
                required={required}
                aria-invalid={!!error}
                aria-describedby={error ? `${name}-error` : undefined}
            />
            {error && (
                <span className="error-message" id={`${name}-error`}>
                    {error}
                </span>
            )}
        </div>
    );
}
```

## Form Validation

### 1. Client-Side Validation
Using Zod for type-safe validation:

```typescript
import { z } from 'zod';

const meetingSchema = z.object({
    title: z.string()
        .min(1, 'Title is required')
        .max(100, 'Title must be less than 100 characters'),
    description: z.string()
        .max(500, 'Description must be less than 500 characters')
        .optional(),
    startTime: z.string()
        .refine(val => new Date(val) > new Date(), {
            message: 'Start time must be in the future'
        }),
    endTime: z.string()
        .refine(val => new Date(val) > new Date(), {
            message: 'End time must be in the future'
        }),
    maxParticipants: z.number()
        .min(2, 'Must allow at least 2 participants')
        .max(100, 'Cannot exceed 100 participants')
});

type MeetingFormData = z.infer<typeof meetingSchema>;

function useMeetingForm() {
    const [data, setData] = useState<MeetingFormData>({
        title: '',
        description: '',
        startTime: '',
        endTime: '',
        maxParticipants: 10
    });
    const [errors, setErrors] = useState<Partial<Record<keyof MeetingFormData, string>>>({});

    const validate = (): boolean => {
        try {
            meetingSchema.parse(data);
            setErrors({});
            return true;
        } catch (error) {
            if (error instanceof z.ZodError) {
                const newErrors = {};
                error.errors.forEach(err => {
                    newErrors[err.path[0]] = err.message;
                });
                setErrors(newErrors);
            }
            return false;
        }
    };

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        if (validate()) {
            // Submit form
        }
    };

    return { data, setData, errors, handleSubmit };
}
```

### 2. Custom Validation Rules
Complex validation logic:

```typescript
function validateMeetingTimes(startTime: string, endTime: string): string | null {
    const start = new Date(startTime);
    const end = new Date(endTime);
    
    if (start >= end) {
        return 'End time must be after start time';
    }
    
    const duration = (end.getTime() - start.getTime()) / (1000 * 60 * 60); // hours
    if (duration > 8) {
        return 'Meeting cannot be longer than 8 hours';
    }
    
    return null;
}

const meetingSchema = z.object({
    startTime: z.string(),
    endTime: z.string()
}).refine(
    data => !validateMeetingTimes(data.startTime, data.endTime),
    {
        message: 'Invalid meeting times',
        path: ['endTime']
    }
);
```

## Form State Management

### 1. Form Context
Managing complex form state:

```typescript
interface FormContextType {
    data: MeetingFormData;
    errors: Record<string, string>;
    touched: Record<string, boolean>;
    setFieldValue: (field: keyof MeetingFormData, value: any) => void;
    setFieldTouched: (field: keyof MeetingFormData) => void;
}

const FormContext = createContext<FormContextType | null>(null);

function FormProvider({ children }: { children: ReactNode }) {
    const [data, setData] = useState<MeetingFormData>(initialData);
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [touched, setTouched] = useState<Record<string, boolean>>({});

    const setFieldValue = useCallback((field: keyof MeetingFormData, value: any) => {
        setData(prev => ({
            ...prev,
            [field]: value
        }));
    }, []);

    const setFieldTouched = useCallback((field: keyof MeetingFormData) => {
        setTouched(prev => ({
            ...prev,
            [field]: true
        }));
    }, []);

    return (
        <FormContext.Provider 
            value={{ 
                data, 
                errors, 
                touched, 
                setFieldValue, 
                setFieldTouched 
            }}
        >
            {children}
        </FormContext.Provider>
    );
}
```

### 2. Form Hooks
Custom hooks for form functionality:

```typescript
function useField<T extends keyof MeetingFormData>(name: T) {
    const context = useContext(FormContext);
    if (!context) throw new Error('useField must be used within FormProvider');

    const { data, errors, touched, setFieldValue, setFieldTouched } = context;

    const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
        setFieldValue(name, e.target.value);
    };

    const handleBlur = () => {
        setFieldTouched(name);
    };

    return {
        value: data[name],
        error: touched[name] ? errors[name] : undefined,
        onChange: handleChange,
        onBlur: handleBlur
    };
}
```

## Best Practices

### 1. Form Organization
- Break forms into smaller components
- Use consistent validation patterns
- Implement proper error handling
- Show validation feedback at appropriate times

### 2. User Experience
- Show validation errors after field is touched
- Provide clear error messages
- Use appropriate input types
- Implement proper form accessibility

### 3. Performance
- Debounce validation when appropriate
- Avoid unnecessary re-renders
- Use memoization for complex validation
- Implement proper form submission states

## Common Pitfalls

### 1. Over-validation
```typescript
// Bad: Validating on every keystroke
<input
    onChange={e => {
        handleChange(e);
        validateField(e.target.name); // Too frequent
    }}
/>

// Good: Validate on blur or submit
<input
    onChange={handleChange}
    onBlur={e => validateField(e.target.name)}
/>
```

### 2. Poor Error Handling
```typescript
// Bad: Generic error messages
if (!isValid) {
    setError('Invalid input');
}

// Good: Specific, actionable error messages
if (password.length < 8) {
    setError('Password must be at least 8 characters long');
}
```

## Next Steps
After mastering forms and validation, proceed to:
1. API Integration (4_api_integration.md)
2. Error Handling (5_error_handling.md)
3. Performance Optimization (6_performance_optimization.md) 