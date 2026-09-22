import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import fa from './fa'
import en from './en'

i18n.use(initReactI18next).init({
  resources: { fa, en },
  lng: 'fa',
  fallbackLng: 'en',
  interpolation: { escapeValue: false },
})

export default i18n