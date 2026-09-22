/**
 * Types for the /api/about endpoint.
 * Mirrors backend/app/api/meta.py AboutResponse.
 */

export interface AboutAuthor {
  name_fa: string;
  name_en: string;
  role_fa: string;
  role_en: string;
  email: string;
  linkedin: string;
  website: string;
}

export interface AboutTechStack {
  frontend: string;
  backend: string;
  python: string;
  database: string;
  nlp: string;
}

export interface AboutResponse {
  app_name: string;
  version: string;
  tagline_fa: string;
  tagline_en: string;
  license: string;
  copyright_year: number;
  author: AboutAuthor;
  tech_stack: AboutTechStack;
  github: string;
}