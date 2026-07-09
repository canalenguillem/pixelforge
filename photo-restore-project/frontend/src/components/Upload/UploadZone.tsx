import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { UploadCloud } from 'lucide-react'
import { cn } from '@/lib/utils'

interface UploadZoneProps {
  onFile: (file: File) => void
  disabled?: boolean
}

/** Zona de subida con drag & drop (react-dropzone). */
export function UploadZone({ onFile, disabled }: UploadZoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) onFile(accepted[0])
    },
    [onFile],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    multiple: false,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/bmp': ['.bmp'],
      'image/tiff': ['.tiff', '.tif'],
    },
  })

  return (
    <div
      {...getRootProps()}
      className={cn(
        'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-border p-12 text-center transition-colors',
        isDragActive && 'border-primary bg-primary/5',
        disabled && 'cursor-not-allowed opacity-50',
      )}
    >
      <input {...getInputProps()} />
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-primary/10">
        <UploadCloud className="h-7 w-7 text-primary" />
      </div>
      <div>
        <p className="font-medium">
          {isDragActive ? 'Suelta la foto aquí' : 'Arrastra una foto antigua o haz clic'}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">JPG, PNG, BMP o TIFF · máx. 50 MB</p>
      </div>
    </div>
  )
}
