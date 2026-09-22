import { useTranslation } from 'react-i18next'
import { AlertTriangle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useConfirmStore } from './confirmStore'

export function ConfirmHost() {
  const { t } = useTranslation()
  const open = useConfirmStore((s) => s.open)
  const options = useConfirmStore((s) => s.options)
  const resolve = useConfirmStore((s) => s.resolve)
  const handleOpenChange = useConfirmStore((s) => s.handleOpenChange)

  const isDestructive = options.variant === 'destructive'

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <div className="flex items-start gap-3">
            {isDestructive && (
              <AlertTriangle
                className="h-5 w-5 mt-0.5 shrink-0"
                style={{ color: 'rgb(var(--color-error))' }}
              />
            )}
            <div className="min-w-0 flex-1">
              <DialogTitle>
                {options.title || t('confirm.defaultTitle')}
              </DialogTitle>
              {options.description && (
                <DialogDescription className="mt-2">
                  {options.description}
                </DialogDescription>
              )}
            </div>
          </div>
        </DialogHeader>

        <DialogFooter>
          <Button
            variant="ghost"
            onClick={() => resolve(false)}
            autoFocus={isDestructive ? false : true}
          >
            {options.cancelLabel || t('common.cancel')}
          </Button>
          <Button
            variant={isDestructive ? 'destructive' : 'default'}
            onClick={() => resolve(true)}
            autoFocus={isDestructive ? true : false}
          >
            {options.confirmLabel || t('common.confirm')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}