"use client";

import type { TailoredResumeSections } from "@/lib/types/resume-sections";

export function ResumePreview({ sections }: { sections: TailoredResumeSections }) {
  const c = sections.contact;
  const contactBits = [c.email, c.phone, c.location, c.linkedin, c.github, c.website].filter(Boolean);

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-900 shadow-sm">
      {c.name && <h2 className="text-center text-xl font-bold text-slate-900">{c.name}</h2>}
      {contactBits.length > 0 && (
        <p className="mt-1 text-center text-xs text-slate-600">{contactBits.join(" | ")}</p>
      )}

      {sections.summary && (
        <section className="mt-5">
          <h3 className="border-b border-slate-200 pb-1 text-xs font-bold uppercase tracking-wide text-slate-900">
            Summary
          </h3>
          <p className="mt-2 leading-relaxed text-slate-800">{sections.summary}</p>
        </section>
      )}

      {sections.skills.length > 0 && (
        <section className="mt-5">
          <h3 className="border-b border-slate-200 pb-1 text-xs font-bold uppercase tracking-wide text-slate-900">
            Skills
          </h3>
          <p className="mt-2 text-slate-800">{sections.skills.join(", ")}</p>
        </section>
      )}

      {sections.experience.length > 0 && (
        <section className="mt-5">
          <h3 className="border-b border-slate-200 pb-1 text-xs font-bold uppercase tracking-wide text-slate-900">
            Experience
          </h3>
          <div className="mt-2 space-y-4">
            {sections.experience.map((exp, i) => (
              <div key={i}>
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <p className="font-semibold text-slate-900">
                    {[exp.title, exp.company].filter(Boolean).join(" — ")}
                  </p>
                  {(exp.start_date || exp.end_date) && (
                    <p className="text-xs text-slate-500">
                      {[exp.start_date, exp.end_date].filter(Boolean).join(" – ")}
                    </p>
                  )}
                </div>
                {exp.location && <p className="text-xs text-slate-500">{exp.location}</p>}
                {exp.bullets.length > 0 && (
                  <ul className="mt-1 list-inside list-disc space-y-0.5 text-slate-800">
                    {exp.bullets.map((b, j) => (
                      <li key={j}>{b}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {sections.education.length > 0 && (
        <section className="mt-5">
          <h3 className="border-b border-slate-200 pb-1 text-xs font-bold uppercase tracking-wide text-slate-900">
            Education
          </h3>
          <div className="mt-2 space-y-3">
            {sections.education.map((edu, i) => (
              <div key={i}>
                <p className="font-semibold text-slate-900">
                  {[edu.degree, edu.institution].filter(Boolean).join(" — ")}
                </p>
                {edu.graduation_date && <p className="text-xs text-slate-500">{edu.graduation_date}</p>}
                {edu.details.length > 0 && (
                  <ul className="mt-1 list-inside list-disc text-slate-800">
                    {edu.details.map((d, j) => (
                      <li key={j}>{d}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {sections.certifications.length > 0 && (
        <section className="mt-5">
          <h3 className="border-b border-slate-200 pb-1 text-xs font-bold uppercase tracking-wide text-slate-900">
            Certifications
          </h3>
          <ul className="mt-2 list-inside list-disc text-slate-800">
            {sections.certifications.map((cert, i) => (
              <li key={i}>{cert}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
