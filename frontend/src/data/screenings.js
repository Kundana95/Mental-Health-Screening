import depressionIllustration from '../assets/depression-illustration.jpeg';
import anxietyIllustration from '../assets/anxiety-illustration.jpeg';
import bipolarIllustration from '../assets/bipolar-illustration.jpeg';
import schizophreniaIllustration from '../assets/schizophrenia-illustration.jpeg';

export const screenings = [
  {
    slug: 'depression',
    eyebrow: 'MOOD & EVERYDAY LIFE',
    title: 'Depression Screening',
    description: 'Make space to reflect on your mood, daily experiences and personal context.',
    detail: '25 required answers · Screening form',
    tone: 'lilac',
    illustration: depressionIllustration,
    illustrationAlt: 'A person sitting curled up on a bed beside a sleeping cat.',
  },
  {
    slug: 'anxiety',
    eyebrow: 'THE STUDENT EXPERIENCE',
    title: 'Anxiety Screening',
    description: 'Reflect on academic experiences with an experimental screening estimate based on a trained model.',
    detail: '7 questionnaire items · Experimental model',
    tone: 'peach',
    illustration: anxietyIllustration,
    illustrationAlt: 'A person sitting with hands on their cheeks beneath tangled thought lines.',
  },
  {
    slug: 'bipolar',
    eyebrow: 'A DIFFERENT PERSPECTIVE',
    title: 'Bipolar Disorder Screening',
    description: 'Explore an experimental screening prototype built from a small research dataset.',
    detail: '10 model inputs · Experimental prototype',
    tone: 'blue',
    illustration: bipolarIllustration,
    illustrationAlt: 'A smiling person shown between a warm sunny sky and a calm night sky.',
  },
  {
    slug: 'schizophrenia',
    eyebrow: 'IN YOUR OWN WORDS',
    title: 'Schizophrenia-related Text',
    description: 'Explore an experimental text classifier trained on Reddit community posts.',
    detail: 'Paragraph input · Experimental classifier',
    tone: 'sage',
    illustration: schizophreniaIllustration,
    illustrationAlt: 'A person seated thoughtfully with soft overlapping portraits in the background.',
  },
];
