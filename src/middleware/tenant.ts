import type { NextFunction, Request, Response } from 'express';

export function requireTenant(req: Request, res: Response, next: NextFunction) {
  const userId = req.header('x-user-id');
  if (!userId) {
    return res.status(401).json({ error: 'Missing x-user-id tenant header' });
  }
  req.userId = userId;
  next();
}
