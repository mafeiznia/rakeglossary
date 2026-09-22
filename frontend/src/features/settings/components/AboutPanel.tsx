import { useTranslation } from 'react-i18next'
import { BookOpen, Mail, Briefcase, Globe, Code } from 'lucide-react'
import { useAbout } from '@/hooks/useAbout'

/**
 * About panel shown at the bottom of the Settings page.
 *
 * Renders three cards:
 *  - Hero (icon + app name + version + tagline)
 *  - Author (name + role + email / LinkedIn / website)
 *  - Tech stack + License + GitHub link
 *
 * All static labels use i18n keys under `about.*`
 * (added in D.8 step 5).
 */
export function AboutPanel() {
  const { t, i18n } = useTranslation()
  const { data: about } = useAbout()
  const isFa = i18n.language === 'fa'

  return (
    <section className="space-y-3">
      <h3 className="text-lg font-semibold">{t('about.title')}</h3>

      {!about ? (
        <div
          className="rounded-lg border p-6 text-center text-sm"
          style={{
            backgroundColor: 'rgb(var(--color-surface))',
            borderColor: 'rgb(var(--color-border))',
            color: 'rgb(var(--color-text-muted))',
          }}
        >
          {t('about.loading')}
        </div>
      ) : (
        <>
          {/* --- Hero --- */}
          <div
            className="rounded-lg border p-6 text-center space-y-2"
            style={{
              backgroundColor: 'rgb(var(--color-surface))',
              borderColor: 'rgb(var(--color-border))',
            }}
          >
            <BookOpen
              className="h-10 w-10 mx-auto"
              style={{ color: 'rgb(var(--color-primary))' }}
            />
            <h4 className="text-xl font-bold">{about.app_name}</h4>
            <p
              className="text-sm"
              style={{ color: 'rgb(var(--color-text-muted))' }}
            >
              {t('about.versionLabel')} {about.version}
            </p>
            <p className="text-sm pt-2">
              {isFa ? about.tagline_fa : about.tagline_en}
            </p>
          </div>

          {/* --- Author --- */}
          <div
            className="rounded-lg border p-4 space-y-2"
            style={{
              backgroundColor: 'rgb(var(--color-surface))',
              borderColor: 'rgb(var(--color-border))',
            }}
          >
            <h4
              className="text-sm font-semibold"
              style={{ color: 'rgb(var(--color-primary))' }}
            >
              {isFa ? about.author.role_fa : about.author.role_en}
            </h4>

            {isFa ? (
              <>
                <p className="text-base font-medium">{about.author.name_fa}</p>
                <p
                  className="text-xs"
                  style={{ color: 'rgb(var(--color-text-muted))' }}
                >
                  {about.author.name_en}
                </p>
              </>
            ) : (
              <p className="text-base font-medium">{about.author.name_en}</p>
            )}

            <div className="flex flex-col gap-1.5 pt-2">
              <a
                href={`mailto:${about.author.email}`}
                className="flex items-center gap-2 text-sm hover:underline"
                style={{ color: 'rgb(var(--color-text))' }}
              >
                <Mail className="h-3.5 w-3.5 shrink-0" />
                <span dir="ltr">{about.author.email}</span>
              </a>
              <a
                href={about.author.linkedin}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 text-sm hover:underline"
                style={{ color: 'rgb(var(--color-text))' }}
              >
                <Briefcase className="h-3.5 w-3.5 shrink-0" />
                <span>LinkedIn</span>
              </a>
              <a
                href={about.author.website}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 text-sm hover:underline"
                style={{ color: 'rgb(var(--color-text))' }}
              >
                <Globe className="h-3.5 w-3.5 shrink-0" />
                <span dir="ltr">yadoto.ir</span>
              </a>
            </div>
          </div>

          {/* --- Tech stack --- */}
          <div
            className="rounded-lg border p-4 space-y-2"
            style={{
              backgroundColor: 'rgb(var(--color-surface))',
              borderColor: 'rgb(var(--color-border))',
            }}
          >
            <h4 className="text-sm font-semibold">
              {t('about.techStack')}
            </h4>
            <dl className="text-sm space-y-1.5">
              <TechRow label={t('about.frontend')} value={about.tech_stack.frontend} />
              <TechRow label={t('about.backend')} value={about.tech_stack.backend} />
              <TechRow label={t('about.python')} value={about.tech_stack.python} />
              <TechRow label={t('about.database')} value={about.tech_stack.database} />
              <TechRow label={t('about.nlp')} value={about.tech_stack.nlp} />
            </dl>
          </div>

          {/* --- License --- */}
          <div
            className="rounded-lg border p-4 space-y-1"
            style={{
              backgroundColor: 'rgb(var(--color-surface))',
              borderColor: 'rgb(var(--color-border))',
            }}
          >
            <h4 className="text-sm font-semibold">{t('about.license')}</h4>
            <p className="text-sm">{about.license} License</p>
            <p
              className="text-xs"
              style={{ color: 'rgb(var(--color-text-muted))' }}
            >
              © {about.copyright_year} {about.author.name_en}
            </p>
          </div>

          {/* --- GitHub link --- */}
          {about.github && (
            <div className="text-center pt-1">
              <a
                href={about.github}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 text-sm hover:underline"
                style={{ color: 'rgb(var(--color-text-muted))' }}
              >
                <Code className="h-3.5 w-3.5" />
                {t('about.sourceCode')}
              </a>
            </div>
          )}
        </>
      )}
    </section>
  )
}

function TechRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt style={{ color: 'rgb(var(--color-text-muted))' }}>{label}</dt>
      <dd className="text-end" dir="ltr">
        {value}
      </dd>
    </div>
  )
}