import { showComponentError, getSections } from 'utils';
import studentAssignment from "teaching/studentAssignment";
import studentGroups from "teaching/studentGroups";
import gradebook from "teaching/gradebook";
import submissions from "teaching/submissions";
import assignmentForm from "teaching/assignmentForm";

$(document).ready(function () {
  let sections = getSections();
  if (sections.includes('tooltips')) {
    let defaultWhiteList = $.fn.tooltip.Constructor.DEFAULTS.whiteList;
    defaultWhiteList.dl = ['class'];
    defaultWhiteList.dd = [];
    defaultWhiteList.dt = [];
    $('[data-toggle="tooltip"]').tooltip();
  }
  if (sections.includes("studentAssignment")) {
    try {
      studentAssignment.launch();
    } catch (error) {
      showComponentError(error);
    }
  } else if (sections.includes("studentGroups")) {
    try {
      studentGroups();
    } catch (error) {
      showComponentError(error);
    }
  }

  if (sections.includes("gradebook")) {
    try {
      gradebook.launch();
    } catch (error) {
      showComponentError(error);
    }
  } else if (sections.includes("submissions")) {
    try {
      submissions.launch();
    } catch (error) {
      showComponentError(error);
    }
  } else if (sections.includes("assignmentForm")) {
    try {
      assignmentForm();
    } catch (error) {
      showComponentError(error);
    }
  }
});
