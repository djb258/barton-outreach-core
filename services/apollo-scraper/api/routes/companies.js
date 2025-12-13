const express = require('express');
const router = express.Router();
const { renderClient } = require('../clients/renderClient');

/**
 * GET /api/v1/companies
 * Get all companies from Render marketing DB
 */
router.get('/', async (req, res) => {
  try {
    const companies = await renderClient.getCompanies();
    res.json(companies);
  } catch (error) {
    console.error('Error fetching companies:', error);
    res.status(500).json({
      error: error.message || 'Failed to fetch companies'
    });
  }
});

/**
 * POST /api/v1/companies
 * Create a new company in Render marketing DB
 */
router.post('/', async (req, res) => {
  try {
    const result = await renderClient.createCompany(req.body);
    res.status(201).json(result);
  } catch (error) {
    console.error('Error creating company:', error);
    res.status(500).json({
      error: error.message || 'Failed to create company'
    });
  }
});

/**
 * PUT /api/v1/companies/:id
 * Update a company in Render marketing DB
 */
router.put('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const result = await renderClient.updateCompany(id, req.body);
    res.json(result);
  } catch (error) {
    console.error('Error updating company:', error);
    res.status(500).json({
      error: error.message || 'Failed to update company'
    });
  }
});

module.exports = router;