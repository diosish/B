import React from 'react'
import type { JSONSchema7 } from 'json-schema'
import { useForm } from 'react-hook-form'

interface Props {
  schema: JSONSchema7
  defaultValues?: Record<string, any>
  onSubmit: (data: any) => void
}

export function FormRenderer({ schema, defaultValues, onSubmit }: Props) {
  const { register, handleSubmit } = useForm({ defaultValues })
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {Object.entries(schema.properties || {}).map(([key, subschema]: any) => (
        <div key={key} style={{ margin: '8px 0' }}>
          <label>{subschema.title || key}</label><br/>
          <input
            {...register(key, { required: schema.required?.includes(key) })}
            type={subschema.type === 'number' ? 'number' : 'text'}
          />
        </div>
      ))}
      <button type="submit">Сохранить</button>
    </form>
  )
}
