export type ProfileId = 'organiser' | 'teammate' | 'observer';
export type Stage = 'brief' | 'research' | 'negotiation' | 'decision' | 'decided';
export type Vendor = {
  liaisonStatus?: 'discovered'|'awaiting_reply'|'negotiating'|'ready';
  id: string; name: string; initials: string; location: string; color: string;
  executionMode?: 'demo' | 'live'; sourceUrl?: string; evidenceExcerpt?: string; quantity?: number; validUntil?: string; serverFit?: string; goodsSen: number; deliverySen: number | null; initialSen: number;
  arrival: string | null; specsConfirmed: boolean; status: string; description: string;
  strengths: string[]; concerns: string[]; quoteRef: string;
};
export type Activity = { id: string; title: string; detail: string; time: string; kind: 'research' | 'mail' | 'offer' | 'human' };
export type ProcurementCase = {
  taskWorkflowVersion?: number;selectionTarget?:number;
  approvalQueue?: {vendorId:string;status:'approval_needed'|'waitlist'|'approved'|'secured'|'rejected'|'not_selected'|'liaising'|'needs_terms';reason:string;rank?:number;termsHash?:string}[];
  vendorDecisions?:{id:string;vendorId:string;status:string;termsHash:string;approvedAt:string;confirmedAt?:string;confirmationMessageId?:string;executionMode:string}[];
  taskId?:string|null;workflowMode?:'research'|'liaise';workflowPlan?:{id:string;label:string;status:string;detail:string}[];shortlistVendorIds?:string[];
  backendRevision?: number; eventId?: string; messages?: {id:string;vendorId:string;direction:string;body:string;time:string;executionMode:string}[]; id: string; title: string; goal: string; quantity: number; budgetSen: number; targetSen: number;
  deadline: string; location: string; stage: Stage; selectedVendorId: string | null;
  vendors: Vendor[]; events: Activity[];
  draft: { recipient: string; subject: string; body: string; status: 'pending' | 'approved' | 'rejected' | 'sent'; vendorId?: string; sentId?: string; revision: number };
};
export type DemoState = { version: 2; cases: ProcurementCase[] };
export type NewBrief = { title: string; goal: string; quantity: number; budgetSen: number; targetSen: number; deadline: string; location: string };
export type Action =
  | {type:'liaise-task';caseId:string}
  | {type:'approve-vendor'|'reject-vendor'|'confirm-vendor';caseId:string;vendorId:string}
  | { type: 'research' | 'approve' | 'reject' | 'send' | 'sync'; caseId: string }
  | { type: 'choose'; caseId: string; vendorId: string }
  | { type: 'prepare'; caseId: string; vendorId: string }
  | { type: 'edit-draft'; caseId: string; body: string }
  | { type: 'create'; brief: NewBrief; id: string };

export const profiles = [
  { id: 'organiser' as const, name: 'Aina Rahman', initials: 'AR', role: 'Organiser', description: 'Approve messages & make final decisions' },
  { id: 'teammate' as const, name: 'Daniel Tan', initials: 'DT', role: 'Teammate', description: 'Create briefs, research & edit drafts' },
  { id: 'observer' as const, name: 'Guest', initials: 'G', role: 'Observer', description: 'View cases, offers & evidence' },
];

export const money = (sen: number | null) => sen === null ? 'Quote needed' : new Intl.NumberFormat('en-MY', { style: 'currency', currency: 'MYR', minimumFractionDigits: 0, maximumFractionDigits: 2 }).format(sen / 100);
export const dateLabel = (date: string | null) => date ? new Intl.DateTimeFormat('en-MY', { day: 'numeric', month: 'short', timeZone: 'Asia/Kuala_Lumpur' }).format(new Date(date + 'T12:00:00+08:00')) : 'To confirm';
export const totalCost = (offer: { executionMode?: 'demo' | 'live'; sourceUrl?: string; evidenceExcerpt?: string; quantity?: number; validUntil?: string; serverFit?: string; goodsSen: number; deliverySen: number | null }): number | null => offer.deliverySen === null ? null : offer.goodsSen + offer.deliverySen;
export const validDate = (value: string) => /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0,10) === value;
export function fitReason(brief: ProcurementCase, vendor: Vendor): string {
  if(vendor.serverFit) return vendor.serverFit;
  if(vendor.quantity && vendor.quantity!==brief.quantity) return 'Quantity mismatch';
  const cost=totalCost(vendor);
  if(cost===null || vendor.arrival===null) return 'Missing terms';
  if(cost>brief.budgetSen) return 'Above budget';
  if(vendor.arrival>brief.deadline) return 'Arrives too late';
  if(!vendor.specsConfirmed) return 'Specifications unconfirmed';
  return 'Meets your brief';
}
export const eligible = (brief: ProcurementCase, vendor: Vendor) => fitReason(brief,vendor)==='Meets your brief';

const vendors = (): Vendor[] => [
  { id: 'campus', name: 'Campus Printworks', initials: 'CP', location: 'Subang Jaya', color: 'peach', goodsSen: 145000, deliverySen: 10000, initialSen: 165000, arrival: '2026-10-22', specsConfirmed: true, status: 'Final offer', description: 'Local printing studio with a fast turnaround and a hands-on production team.', strengths: ['One-colour printing included', 'Arrives 3 days before deadline', 'Digital artwork proof'], concerns: ['RM50 above your hard budget', 'No further price reduction offered'], quoteRef: 'DEMO-CP-002' },
  { id: 'meridian', name: 'Meridian Merchandise', initials: 'MM', location: 'Kuala Lumpur', color: 'lilac', goodsSen: 134000, deliverySen: null, initialSen: 134000, arrival: null, specsConfirmed: true, status: 'Details pending', description: 'Promotional merchandise supplier offering competitive base pricing.', strengths: ['Lowest advertised goods price', 'Custom logo printing included'], concerns: ['Delivery charges not confirmed', 'Arrival date still pending'], quoteRef: 'DEMO-MM-001' },
  { id: 'willow', name: 'Willow Supply Studio', initials: 'WS', location: 'Petaling Jaya', color: 'sage', goodsSen: 140000, deliverySen: 5000, initialSen: 180000, arrival: '2026-10-23', specsConfirmed: true, status: 'Terms confirmed', description: 'Small-batch merchandise studio specialising in thoughtful, practical event goods.', strengths: ['RM1,450 all-in quotation', 'Delivery and printing included', 'Arrives 2 days before deadline'], concerns: ['Quote valid until 15 October', 'Artwork approval required before production'], quoteRef: 'DEMO-WS-003' },
];

const draft = () => ({ recipient: 'Willow Supply Studio · controlled demo recipient', subject: 'Artwork proof for 300 custom tote bags', body: 'Hi Willow team,\n\nThank you for the revised all-in quotation of RM1,450 for 300 cotton tote bags with one-colour printing, delivered to Subang Jaya by 23 October.\n\nCould you share a digital artwork proof and confirm the production timeline after we review it? This is an enquiry only; our organising team will make the final vendor decision.\n\nThank you,\nAina\nTechnology Club', status: 'pending' as const, revision: 1 });
const events = (): Activity[] => [
  { id: 'e1', title: 'Your brief, understood', detail: '300 cotton tote bags. RM1,500 ceiling. Arrive by 25 October.', time: '10:02', kind: 'research' },
  { id: 'e2', title: 'Three suppliers compared', detail: 'Printing, landed cost and delivery checked against your brief.', time: '10:04', kind: 'research' },
  { id: 'e3', title: 'Campus reached its price floor', detail: 'RM1,550 final offer. Above budget, so outreach moved to a backup.', time: '10:08', kind: 'mail' },
  { id: 'e4', title: 'A better offer from Willow', detail: 'RM1,800 → RM1,450, with the same quantity and printing.', time: '10:12', kind: 'offer' },
  { id: 'e5', title: 'Ready for your judgement', detail: 'Offers collected. The final choice belongs to your team.', time: '10:14', kind: 'human' },
];

export function initialState(): DemoState {
  return { version: 2, cases: [
    { id: 'case-totes', title: 'Totes for the tech crowd', goal: 'Find 300 cotton tote bags with a one-colour club logo for our technology event. Compare vendors, collect quotes and negotiate within RM1,500. Deliver to Subang Jaya on or before 25 October.', quantity: 300, budgetSen: 150000, targetSen: 135000, deadline: '2026-10-25', location: 'Subang Jaya, Selangor', stage: 'decision', selectedVendorId: null, vendors: vendors(), events: events(), draft: draft() },
    { id: 'case-workshop', title: 'A little fuel for big ideas', goal: 'Find a catering partner for a 50-person student workshop. Vegetarian options required. We need comparable quotes before making a decision.', quantity: 50, budgetSen: 80000, targetSen: 70000, deadline: '2026-10-28', location: 'Taylor’s University', stage: 'brief', selectedVendorId: null, vendors: [], events: [], draft: { ...draft(), body: '', subject: 'Quotation enquiry', recipient: 'No vendor yet' } },
  ] };
}

export function applyAction(state: DemoState, actor: ProfileId, action: Action): DemoState {
  if (actor === 'observer') throw new Error('This profile is view-only. Switch to Organiser or Teammate.');
  if ((action.type === 'choose' || action.type === 'approve' || action.type === 'reject') && actor !== 'organiser') throw new Error('Only the organiser can approve outreach or make the final decision.');
  const next = structuredClone(state);
  if (action.type === 'create') {
    const b = action.brief;
    if (!b.title.trim() || !b.goal.trim() || !b.location.trim() || !Number.isSafeInteger(b.quantity) || b.quantity <= 0 || !Number.isSafeInteger(b.budgetSen) || b.budgetSen <= 0 || !Number.isSafeInteger(b.targetSen) || b.targetSen <= 0 || b.targetSen > b.budgetSen || !validDate(b.deadline) || b.deadline <= '2026-10-10') throw new Error('Check your brief, quantity, budget, target, delivery date and location.');
    next.cases.unshift({ ...b, id: action.id, stage: 'brief', selectedVendorId: null, vendors: [], events: [], draft: { ...draft(), subject: `Quotation enquiry: ${b.title}`, body: '', recipient: 'No vendor yet' } });
    return next;
  }
  const c = next.cases.find(c => c.id === action.caseId);
  if (!c) throw new Error('Case not found.');
  const log = (title: string, detail: string, kind: Activity['kind']) => c.events.push({ id: `event-${Date.now()}-${c.events.length}`, title, detail, time: new Intl.DateTimeFormat('en-MY', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'Asia/Kuala_Lumpur' }).format(new Date()), kind });
  if (action.type === 'research') {
    if(c.id !== 'case-totes') throw new Error('Demo research is available only for the tote-bag sample. Live research comes next.');
    c.vendors = vendors();
    c.stage = c.selectedVendorId ? 'decided' : 'decision';
    if (!c.draft.body) c.draft = draft();
    log('Demo research prepared', 'Illustrative tote-bag offers loaded. No live search or email was performed; no vendor selected.', 'research');
  } else if (action.type === 'choose') {
    const v = c.vendors.find(v => v.id === action.vendorId);
    if (!v || !eligible(c, v)) throw new Error('This offer does not meet the confirmed budget and delivery requirements.');
    c.selectedVendorId = v.id; c.stage = 'decided';
    log('Your team made the decision', `${profiles.find(p => p.id === actor)!.name} selected ${v.name}. This records a preference, not a purchase.`, 'human');
  } else if (action.type === 'edit-draft') {
    if (!action.body.trim()) throw new Error('The message cannot be empty.');
    c.draft.body = action.body; c.draft.revision += 1; c.draft.status = 'pending';
  } else {
    if (!c.draft.body.trim()) throw new Error('Prepare a message first.');
    c.draft.status = action.type === 'approve' ? 'approved' : 'rejected';
    log(action.type === 'approve' ? 'Message approved by organiser' : 'Message returned for revision', 'Recorded locally for the demo. No external email was sent.', 'human');
  }
  return next;
}

export function restoreState(raw: string | null): DemoState {
  if (!raw) return initialState();
  try {
    const parsed = JSON.parse(raw) as DemoState;
    if (parsed.version !== 2 || !Array.isArray(parsed.cases) || !parsed.cases.length) return initialState();
    for (const c of parsed.cases) {
      if (typeof c.id !== 'string' || typeof c.title !== 'string' || typeof c.goal !== 'string' || !Number.isSafeInteger(c.budgetSen) || !Number.isSafeInteger(c.quantity) || !validDate(c.deadline) || !Array.isArray(c.vendors) || !Array.isArray(c.events) || !c.draft || typeof c.draft.body !== 'string') return initialState();
      if(typeof c.location!=='string' || !Number.isSafeInteger(c.targetSen) || c.targetSen<=0 || c.targetSen>c.budgetSen || c.quantity<=0 || c.budgetSen<=0 || !['brief','research','negotiation','decision','decided'].includes(c.stage) || !['pending','approved','rejected','sent'].includes(c.draft.status) || !Number.isSafeInteger(c.draft.revision) || c.draft.revision<1 || typeof c.draft.subject!=='string' || typeof c.draft.recipient!=='string') return initialState();
      for(const e of c.events) if(!e || !['id','title','detail','time'].every(k=>typeof e[k as keyof Activity]==='string') || !['research','mail','offer','human'].includes(e.kind)) return initialState();
      if(c.selectedVendorId!==null && (typeof c.selectedVendorId!=='string' || !c.vendors.some(v=>v.id===c.selectedVendorId && eligible(c,v)))) return initialState();
      if((c.stage==='decided') !== (c.selectedVendorId!==null)) return initialState();
      for (const v of c.vendors) if (!v || !['initials','location','color','status','description','quoteRef'].every(k=>typeof v[k as keyof Vendor]==='string') || typeof v.specsConfirmed!=='boolean' || !Number.isSafeInteger(v.initialSen) || !(v.arrival===null || (typeof v.arrival==='string' && validDate(v.arrival))) || !v.strengths.every(x=>typeof x==='string') || !v.concerns.every(x=>typeof x==='string') || typeof v.id !== 'string' || typeof v.name !== 'string' || !Array.isArray(v.strengths) || !Array.isArray(v.concerns) || !Number.isSafeInteger(v.goodsSen) || !(v.deliverySen === null || Number.isSafeInteger(v.deliverySen))) return initialState();
    }
    return parsed;
  } catch { return initialState(); }
}
