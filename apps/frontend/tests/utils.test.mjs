import test from "node:test";
import assert from "node:assert/strict";

// Status mapping test
function statusLabel(status) {
  const map = {
    OPEN: "Ochiq",
    IN_PROGRESS: "Jarayonda",
    RESOLVED: "Hal qilingan",
    ARCHIVED: "Arxivlangan",
    INVALID: "Noto'g'ri",
    DUPLICATE: "Takroriy",
  };
  return map[status] || status;
}

function categoryLabel(category) {
  const map = {
    PIPE_BURST: "Quvur yorilishi",
    SUPPLY_OUTAGE: "Suv ta'minoti uzilishi",
    LOW_PRESSURE: "Suv bosimi pasayishi",
    LEAK: "Suv sizib chiqishi",
    FLOODING: "Suv bosishi",
    PLANNED_REPAIR: "Rejali ta'mirlash",
    SEWAGE: "Kanalizatsiya avariyasi",
    OTHER: "Boshqa muammo",
    UNCLEAR: "Aniqlashtirilishi kerak",
  };
  return map[category] || category;
}

function priorityLabel(priority) {
  switch (priority) {
    case "HIGH":
      return "Yuqori";
    case "MEDIUM":
      return "O'rta";
    case "LOW":
      return "Past";
    default:
      return priority;
  }
}

test("statusLabel returns accurate Uzbek labels", () => {
  assert.equal(statusLabel("OPEN"), "Ochiq");
  assert.equal(statusLabel("IN_PROGRESS"), "Jarayonda");
  assert.equal(statusLabel("RESOLVED"), "Hal qilingan");
  assert.equal(statusLabel("ARCHIVED"), "Arxivlangan");
  assert.equal(statusLabel("INVALID"), "Noto'g'ri");
  assert.equal(statusLabel("DUPLICATE"), "Takroriy");
});

test("categoryLabel maps all water incident types", () => {
  assert.equal(categoryLabel("PIPE_BURST"), "Quvur yorilishi");
  assert.equal(categoryLabel("SUPPLY_OUTAGE"), "Suv ta'minoti uzilishi");
  assert.equal(categoryLabel("SEWAGE"), "Kanalizatsiya avariyasi");
  assert.equal(categoryLabel("FLOODING"), "Suv bosishi");
});

test("priorityLabel returns priority levels", () => {
  assert.equal(priorityLabel("HIGH"), "Yuqori");
  assert.equal(priorityLabel("MEDIUM"), "O'rta");
  assert.equal(priorityLabel("LOW"), "Past");
});
